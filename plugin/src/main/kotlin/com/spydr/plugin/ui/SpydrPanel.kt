package com.spydr.plugin.ui

import com.intellij.notification.NotificationGroupManager
import com.intellij.notification.NotificationType
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.fileEditor.FileEditorManager
import com.intellij.openapi.progress.ProgressIndicator
import com.intellij.openapi.progress.ProgressManager
import com.intellij.openapi.progress.Task
import com.intellij.openapi.project.Project
import com.intellij.openapi.vfs.LocalFileSystem
import com.spydr.plugin.backend.BackendListener
import com.spydr.plugin.backend.ConfigWriter
import com.spydr.plugin.backend.PythonEnvironmentManager
import com.spydr.plugin.backend.PythonProcessManager
import com.spydr.plugin.settings.SpydrSettingsState
import java.nio.file.Path
import javax.swing.JComponent
import javax.swing.SwingUtilities

/**
 * Main SpyDR chat panel that manages the [PythonProcessManager] lifecycle.
 * Context controls are exposed via [settingsComponent] and shown
 * in a separate tool-window tab ("Контекст").
 *
 * Stderr and diagnostic information is routed to [LogPanel]
 * (displayed in a separate "Логи" tab), NOT into the chat.
 */
class SpydrPanel(
    private val project: Project,
    private val logPanel: LogPanel,
) : BackendListener {

    private val settingsPanel = SettingsPanel(project)
    private val chatPanel = ChatPanel(
        onSend = ::handleSend,
        onClear = ::handleClear,
        onStop = ::handleStop,
        onRestart = ::handleRestart,
    )
    private var processManager: PythonProcessManager? = null
    private var assistantMessageStarted = false

    /** Remembered from the last successful setup so we can restart quickly. */
    private var lastPythonPath: String? = null
    private var lastWorkingDir: String? = null

    // -----------------------------------------------------------------------
    // Root component
    // -----------------------------------------------------------------------

    val rootComponent: JComponent = chatPanel.component
    val settingsComponent: JComponent = settingsPanel.component

    init {
        initBackend()
    }

    // -----------------------------------------------------------------------
    // Backend lifecycle
    // -----------------------------------------------------------------------

    private fun initBackend() {
        val settings = SpydrSettingsState.getInstance()

        if (settings.isAutoMode) {
            chatPanel.setStatus("Подготовка окружения…")
            chatPanel.setBusy(true)
            logPanel.append("Запуск автонастройки окружения…", LogPanel.Level.INFO)

            ProgressManager.getInstance().run(object : Task.Backgroundable(
                project, "SpyDR: Настройка окружения", false
            ) {
                override fun run(indicator: ProgressIndicator) {
                    val result = PythonEnvironmentManager.instance.ensureReady(
                        pluginVersion = "1.0.0",
                        indicator = indicator,
                    )

                    if (result.success) {
                        ConfigWriter.writeConfigs(Path.of(result.workingDir))
                        logPanel.append("Конфиги записаны в ${result.workingDir}", LogPanel.Level.INFO)
                    }

                    SwingUtilities.invokeLater {
                        if (result.success) {
                            chatPanel.clearStatus()
                            chatPanel.setBusy(false)
                            startBackend(result.pythonPath, result.workingDir)
                        } else {
                            chatPanel.clearStatus()
                            chatPanel.setBusy(false)
                            logPanel.append("Ошибка настройки: ${result.errorMessage}", LogPanel.Level.ERROR)
                            chatPanel.beginAssistantMessage()
                            chatPanel.appendAssistantText(
                                "❌ Ошибка настройки окружения. Подробности во вкладке «Логи».\n\n" +
                                "Убедитесь, что Python 3.10+ установлен, или укажите путь " +
                                "вручную в Settings → Tools → SpyDR Agent."
                            )
                            chatPanel.endAssistantMessage()
                        }
                    }
                }
            })
        } else {
            val workingDir = project.basePath ?: "."
            ConfigWriter.writeConfigs(Path.of(workingDir))
            startBackend(settings.pythonPath, workingDir)
        }
    }

    private fun startBackend(pythonPath: String, workingDir: String) {
        lastPythonPath = pythonPath
        lastWorkingDir = workingDir

        val settings = SpydrSettingsState.getInstance()
        val env = settings.buildEnvOverrides(projectRoot = project.basePath)

        logPanel.append("Запуск backend: $pythonPath", LogPanel.Level.INFO)

        processManager = PythonProcessManager(
            pythonPath = pythonPath,
            workingDir = workingDir,
            listener = this,
            extraEnv = env,
        )
        processManager?.start()
    }

    private fun restartBackend() {
        processManager?.stop()
        processManager = null

        logPanel.append("Перезапуск backend…", LogPanel.Level.INFO)

        val py = lastPythonPath
        val wd = lastWorkingDir

        if (py != null && wd != null) {
            ConfigWriter.writeConfigs(Path.of(wd))
            startBackend(py, wd)
        } else {
            initBackend()
        }
    }

    // -----------------------------------------------------------------------
    // User actions
    // -----------------------------------------------------------------------

    private fun handleSend(text: String) {
        chatPanel.addUserMessage(text)
        chatPanel.setBusy(true)
        assistantMessageStarted = false

        processManager?.sendChat(
            message = text,
            projectId = settingsPanel.selectedProject,
            featureFilePath = settingsPanel.featureFilePath,
            validationEnabled = settingsPanel.validationEnabled,
            maxValidationIterations = settingsPanel.maxValidationIterations,
        )
    }

    private fun handleClear() {
        chatPanel.clearMessages()
        chatPanel.clearStatus()
        processManager?.sendReset()
    }

    private fun handleStop() {
        if (assistantMessageStarted) {
            chatPanel.appendAssistantText("\n\n⏹ Остановлено")
            chatPanel.endAssistantMessage()
            assistantMessageStarted = false
        }

        chatPanel.clearStatus()
        chatPanel.setBusy(false)
        logPanel.append("Остановлено пользователем", LogPanel.Level.WARN)

        restartBackend()
    }

    private fun handleRestart() {
        chatPanel.clearMessages()
        chatPanel.clearStatus()
        chatPanel.setBusy(false)
        assistantMessageStarted = false

        restartBackend()
    }

    // -----------------------------------------------------------------------
    // BackendListener
    // -----------------------------------------------------------------------

    override fun onText(content: String) {
        SwingUtilities.invokeLater {
            if (!assistantMessageStarted) {
                chatPanel.beginAssistantMessage()
                assistantMessageStarted = true
            }
            chatPanel.appendAssistantText(content)
        }
    }

    override fun onStatus(content: String) {
        SwingUtilities.invokeLater {
            chatPanel.setStatus(content)
        }
    }

    override fun onFeatureWritten(path: String) {
        SwingUtilities.invokeLater {
            chatPanel.setStatus("Feature записан: $path")
        }
        logPanel.append("Feature записан: $path", LogPanel.Level.INFO)
        ApplicationManager.getApplication().invokeLater {
            val vf = LocalFileSystem.getInstance().refreshAndFindFileByPath(path)
            if (vf != null) {
                FileEditorManager.getInstance(project).openFile(vf, true)
            }
        }
    }

    override fun onDone() {
        SwingUtilities.invokeLater {
            if (assistantMessageStarted) {
                chatPanel.endAssistantMessage()
                assistantMessageStarted = false
            }
            chatPanel.clearStatus()
            chatPanel.setBusy(false)
        }
    }

    override fun onError(content: String) {
        SwingUtilities.invokeLater {
            if (!assistantMessageStarted) {
                chatPanel.beginAssistantMessage()
                assistantMessageStarted = true
            }
            chatPanel.appendAssistantText("\n❌ $content")
        }
    }

    override fun onReady(projects: List<String>) {
        SwingUtilities.invokeLater {
            settingsPanel.setProjects(projects)
            chatPanel.setStatus("")
        }
        logPanel.append("Backend готов. Проекты: $projects", LogPanel.Level.INFO)
    }

    override fun onSessionReset() {
        SwingUtilities.invokeLater {
            chatPanel.clearStatus()
        }
        logPanel.append("Сессия сброшена", LogPanel.Level.INFO)
    }

    /** Every stderr line → Logs tab (in real time). */
    override fun onStderrLine(line: String) {
        logPanel.append(line, LogPanel.Level.STDERR)
    }

    /**
     * Process crashed → brief message in chat + IDE notification.
     * Full traceback is already in the Logs tab via [onStderrLine].
     */
    override fun onProcessDied(exitCode: Int, lastStderr: String) {
        logPanel.append("--- Процесс завершился с кодом $exitCode ---", LogPanel.Level.ERROR)

        SwingUtilities.invokeLater {
            if (assistantMessageStarted) {
                chatPanel.endAssistantMessage()
                assistantMessageStarted = false
            }
            chatPanel.clearStatus()
            chatPanel.setBusy(false)

            chatPanel.beginAssistantMessage()
            chatPanel.appendAssistantText(
                "❌ Backend завершился с кодом $exitCode.\n" +
                "Подробности во вкладке «Логи».\n" +
                "Нажмите «Перезапуск» для восстановления."
            )
            chatPanel.endAssistantMessage()
        }

        // IDE balloon notification
        try {
            NotificationGroupManager.getInstance()
                .getNotificationGroup("SpyDR Agent")
                .createNotification(
                    "SpyDR Agent",
                    "Python-процесс завершился с кодом $exitCode. Подробности во вкладке «Логи».",
                    NotificationType.ERROR,
                )
                .notify(project)
        } catch (_: Exception) {
            // NotificationGroup might not be registered — not critical
        }
    }
}
