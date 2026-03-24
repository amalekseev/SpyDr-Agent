package com.spydr.plugin.ui

import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.fileEditor.FileEditorManager
import com.intellij.openapi.progress.ProgressIndicator
import com.intellij.openapi.progress.ProgressManager
import com.intellij.openapi.progress.Task
import com.intellij.openapi.project.Project
import com.intellij.openapi.vfs.LocalFileSystem
import com.spydr.plugin.backend.BackendListener
import com.spydr.plugin.backend.PythonEnvironmentManager
import com.spydr.plugin.backend.PythonProcessManager
import com.spydr.plugin.settings.SpydrSettingsState
import java.awt.BorderLayout
import javax.swing.JComponent
import javax.swing.JPanel
import javax.swing.SwingUtilities

/**
 * Main SpyDR panel that composes [SettingsPanel], [ChatPanel],
 * and manages the [PythonProcessManager] lifecycle.
 *
 * On startup, when [SpydrSettingsState.isAutoMode] is `true` (the
 * default), the panel runs [PythonEnvironmentManager.ensureReady]
 * in a background task — extracting the bundled backend, creating
 * a venv, and installing dependencies.  The user sees a progress
 * bar in the IDE while this happens.
 */
class SpydrPanel(private val project: Project) : BackendListener {

    private val settingsPanel = SettingsPanel(project)
    private val chatPanel = ChatPanel(
        onSend = ::handleSend,
        onClear = ::handleClear,
    )
    private var processManager: PythonProcessManager? = null
    private var assistantMessageStarted = false

    // -----------------------------------------------------------------------
    // Root component exposed to the ToolWindowFactory
    // -----------------------------------------------------------------------

    val rootComponent: JComponent

    init {
        rootComponent = JPanel(BorderLayout()).apply {
            add(settingsPanel.component, BorderLayout.NORTH)
            add(chatPanel.component, BorderLayout.CENTER)
        }
        initBackend()
    }

    // -----------------------------------------------------------------------
    // Backend lifecycle
    // -----------------------------------------------------------------------

    /**
     * Decides how to start the Python backend:
     * - **Auto mode** (pythonPath is blank): run the full setup pipeline
     *   in a background task with a progress indicator.
     * - **Custom mode** (pythonPath is set): start the process manager
     *   immediately using the user-supplied path.
     */
    private fun initBackend() {
        val settings = SpydrSettingsState.getInstance()

        if (settings.isAutoMode) {
            // ---- Auto / bundled mode ----
            chatPanel.setStatus("Подготовка окружения…")
            chatPanel.setBusy(true)

            ProgressManager.getInstance().run(object : Task.Backgroundable(
                project, "SpyDR: Настройка окружения", false
            ) {
                override fun run(indicator: ProgressIndicator) {
                    val result = PythonEnvironmentManager.instance.ensureReady(
                        pluginVersion = "1.0.0",
                        indicator = indicator,
                    )

                    SwingUtilities.invokeLater {
                        if (result.success) {
                            chatPanel.clearStatus()
                            chatPanel.setBusy(false)
                            startBackend(result.pythonPath, result.workingDir)
                        } else {
                            chatPanel.clearStatus()
                            chatPanel.setBusy(false)
                            chatPanel.beginAssistantMessage()
                            chatPanel.appendAssistantText(
                                "❌ Ошибка настройки окружения:\n${result.errorMessage}\n\n" +
                                "Убедитесь, что Python 3.10+ установлен, или укажите путь " +
                                "вручную в Settings → Tools → SpyDR Agent."
                            )
                            chatPanel.endAssistantMessage()
                        }
                    }
                }
            })
        } else {
            // ---- Custom mode ----
            startBackend(
                pythonPath = settings.pythonPath,
                workingDir = project.basePath ?: ".",
            )
        }
    }

    private fun startBackend(pythonPath: String, workingDir: String) {
        val settings = SpydrSettingsState.getInstance()

        // Build extra environment variables for the subprocess
        val envVars = mutableMapOf<String, String>()
        val envFilePath = settings.envFilePath.trim()
        if (envFilePath.isNotEmpty()) {
            envVars["SPYDR_DOTENV_PATH"] = envFilePath
        }

        processManager = PythonProcessManager(
            pythonPath = pythonPath,
            workingDir = workingDir,
            listener = this,
            extraEnv = envVars,
        )
        processManager?.start()
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

    // -----------------------------------------------------------------------
    // BackendListener — all callbacks arrive on a background thread,
    // so we must dispatch to EDT.
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
        // Open the file in the editor
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
            chatPanel.appendAssistantText("\n❌ Ошибка: $content")
        }
    }

    override fun onReady(projects: List<String>) {
        SwingUtilities.invokeLater {
            settingsPanel.setProjects(projects)
            chatPanel.setStatus("")
        }
    }

    override fun onSessionReset() {
        SwingUtilities.invokeLater {
            chatPanel.clearStatus()
        }
    }
}
