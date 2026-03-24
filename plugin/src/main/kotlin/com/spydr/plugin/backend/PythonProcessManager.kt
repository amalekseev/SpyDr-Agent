package com.spydr.plugin.backend

import com.intellij.openapi.diagnostic.Logger
import java.io.BufferedReader
import java.io.BufferedWriter
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.nio.charset.StandardCharsets

/**
 * Manages a Python subprocess that runs `src.api.stdio_server`.
 *
 * Communication happens via JSON-lines over stdin/stdout.
 * Stderr is forwarded to the IDE log.
 *
 * @param pythonPath  absolute path to the Python interpreter.
 * @param workingDir  working directory for the subprocess
 *                    (must contain `src/` with the backend code).
 * @param listener    callback interface for incoming messages.
 * @param extraEnv    additional environment variables passed to the
 *                    subprocess (e.g. `SPYDR_DOTENV_PATH`).
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

    companion object {
        private val LOG = Logger.getInstance(PythonProcessManager::class.java)
    }

    // -----------------------------------------------------------------------
    // Lifecycle
    // -----------------------------------------------------------------------

    fun start() {
        if (process != null) return

        try {
            val pb = ProcessBuilder(pythonPath, "-m", "src.api.stdio_server")
                .directory(java.io.File(workingDir))
                .redirectErrorStream(false)

            // Inject extra environment variables (e.g. SPYDR_DOTENV_PATH)
            if (extraEnv.isNotEmpty()) {
                pb.environment().putAll(extraEnv)
            }

            val proc = pb.start()
            process = proc
            writer = BufferedWriter(OutputStreamWriter(proc.outputStream, StandardCharsets.UTF_8))

            // Background thread: read stdout (JSON lines)
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
                }
            }, "SpyDR-stdout-reader").apply {
                isDaemon = true
                start()
            }

            // Background thread: read stderr -> log
            stderrThread = Thread({
                val reader = BufferedReader(InputStreamReader(proc.errorStream, StandardCharsets.UTF_8))
                try {
                    var line: String?
                    while (reader.readLine().also { line = it } != null) {
                        LOG.info("[python stderr] $line")
                    }
                } catch (_: Exception) {
                    // ignore
                }
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

        try {
            proc.outputStream.close()
        } catch (_: Exception) {}

        try {
            proc.destroyForcibly()
        } catch (_: Exception) {}

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
                listener.onError("Backend не запущен")
                return
            }
            synchronized(w) {
                w.write(json)
                w.newLine()
                w.flush()
            }
        } catch (e: Exception) {
            LOG.error("Failed to send to backend", e)
            listener.onError("Ошибка отправки: ${e.message}")
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
