package com.spydr.plugin.backend

import com.intellij.openapi.diagnostic.Logger
import java.io.BufferedReader
import java.io.BufferedWriter
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.nio.charset.StandardCharsets
import java.util.concurrent.ConcurrentLinkedDeque

/**
 * Manages a Python subprocess that runs `src.api.stdio_server`.
 *
 * Communication happens via JSON-lines over stdin/stdout.
 *
 * Stderr is:
 * 1. Written to the IDE diagnostic log (`idea.log`).
 * 2. Forwarded to [BackendListener.onStderrLine] (for the Logs tab).
 * 3. Kept in a ring buffer so that [BackendListener.onProcessDied]
 *    can include the last N lines when the process crashes.
 */
class PythonProcessManager(
    private val pythonPath: String,
    private val workingDir: String,
    private val listener: BackendListener,
    private val extraEnv: Map<String, String> = emptyMap(),
) {
    private var process: Process? = null
    private var writer: BufferedWriter? = null
    private var readerThread: Thread? = null
    private var stderrThread: Thread? = null

    /** Ring buffer keeping the last [MAX_STDERR_LINES] lines of stderr. */
    private val stderrBuffer = ConcurrentLinkedDeque<String>()

    companion object {
        private val LOG = Logger.getInstance(PythonProcessManager::class.java)
        private const val MAX_STDERR_LINES = 80
    }

    // -----------------------------------------------------------------------
    // Lifecycle
    // -----------------------------------------------------------------------

    fun start() {
        if (process != null) return
        stderrBuffer.clear()

        try {
            val pb = ProcessBuilder(pythonPath, "-m", "src.api.stdio_server")
                .directory(java.io.File(workingDir))
                .redirectErrorStream(false)

            if (extraEnv.isNotEmpty()) {
                pb.environment().putAll(extraEnv)
            }

            val proc = pb.start()
            process = proc
            writer = BufferedWriter(OutputStreamWriter(proc.outputStream, StandardCharsets.UTF_8))

            listener.onStderrLine("--- Backend запущен: $pythonPath -m src.api.stdio_server")
            listener.onStderrLine("--- Рабочая директория: $workingDir")

            // stdout reader (JSON-lines)
            readerThread = Thread({
                val reader = BufferedReader(InputStreamReader(proc.inputStream, StandardCharsets.UTF_8))
                try {
                    var line: String?
                    while (reader.readLine().also { line = it } != null) {
                        handleLine(line!!)
                    }
                } catch (e: Exception) {
                    if (process != null) {
                        LOG.warn("stdout reader error", e)
                    }
                } finally {
                    LOG.info("stdout reader finished")
                    onProcessExited()
                }
            }, "SpyDR-stdout-reader").apply {
                isDaemon = true
                start()
            }

            // stderr reader → IDE log + LogPanel + ring buffer
            stderrThread = Thread({
                val reader = BufferedReader(InputStreamReader(proc.errorStream, StandardCharsets.UTF_8))
                try {
                    var line: String?
                    while (reader.readLine().also { line = it } != null) {
                        val l = line!!
                        LOG.info("[python stderr] $l")
                        pushStderrLine(l)
                        listener.onStderrLine(l)
                    }
                } catch (_: Exception) { }
            }, "SpyDR-stderr-reader").apply {
                isDaemon = true
                start()
            }

            LOG.info("Python backend started: $pythonPath -m src.api.stdio_server in $workingDir")

        } catch (e: Exception) {
            LOG.error("Failed to start Python backend", e)
            listener.onError("Не удалось запустить Python: ${e.message}")
        }
    }

    fun stop() {
        val proc = process ?: return
        process = null
        writer = null

        try { proc.outputStream.close() } catch (_: Exception) {}
        try { proc.destroyForcibly() } catch (_: Exception) {}

        readerThread?.interrupt()
        stderrThread?.interrupt()
        readerThread = null
        stderrThread = null

        LOG.info("Python backend stopped")
    }

    // -----------------------------------------------------------------------
    // Sending messages
    // -----------------------------------------------------------------------

    fun sendChat(
        message: String,
        projectId: String,
        featureFilePath: String,
        validationEnabled: Boolean,
        maxValidationIterations: Int,
    ) {
        val json = MessageProtocol.buildChatMessage(
            message = message,
            projectId = projectId,
            featureFilePath = featureFilePath,
            validationEnabled = validationEnabled,
            maxValidationIterations = maxValidationIterations,
        )
        sendLine(json)
    }

    fun sendReset() {
        sendLine(MessageProtocol.buildResetMessage())
    }

    private fun sendLine(json: String) {
        try {
            val w = writer
            if (w == null) {
                listener.onError("Backend не запущен. Нажмите «Перезапуск».")
                return
            }
            synchronized(w) {
                w.write(json)
                w.newLine()
                w.flush()
            }
        } catch (e: Exception) {
            LOG.error("Failed to send to backend", e)
            listener.onError("Ошибка отправки. Подробности во вкладке «Логи».")
        }
    }

    // -----------------------------------------------------------------------
    // Process death detection
    // -----------------------------------------------------------------------

    private fun onProcessExited() {
        val proc = process ?: return

        // Let stderr thread flush its remaining lines
        try { stderrThread?.join(1000) } catch (_: Exception) {}

        val exitCode = try { proc.waitFor() } catch (_: Exception) { -1 }

        if (exitCode != 0) {
            val lastStderr = stderrBuffer.toList().joinToString("\n")
            LOG.warn("Python process exited with code $exitCode")
            listener.onProcessDied(exitCode, lastStderr)
        }

        process = null
        writer = null
    }

    // -----------------------------------------------------------------------
    // Stderr ring buffer
    // -----------------------------------------------------------------------

    private fun pushStderrLine(line: String) {
        stderrBuffer.addLast(line)
        while (stderrBuffer.size > MAX_STDERR_LINES) {
            stderrBuffer.pollFirst()
        }
    }

    // -----------------------------------------------------------------------
    // Parsing incoming messages
    // -----------------------------------------------------------------------

    private fun handleLine(line: String) {
        val msg = MessageProtocol.parse(line) ?: return

        when (msg.type) {
            "text" -> listener.onText(msg.content)
            "status" -> listener.onStatus(msg.content)
            "feature_written" -> listener.onFeatureWritten(msg.path)
            "done" -> listener.onDone()
            "error" -> listener.onError(msg.content)
            "ready" -> listener.onReady(msg.projects)
            "session_reset" -> listener.onSessionReset()
            "projects" -> listener.onReady(msg.projects)
            else -> LOG.warn("Unknown message type: ${msg.type}")
        }
    }
}
