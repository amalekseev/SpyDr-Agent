package com.spydr.plugin

import com.intellij.openapi.project.Project
import com.intellij.openapi.wm.ToolWindow
import com.intellij.openapi.wm.ToolWindowFactory
import com.intellij.ui.content.ContentFactory
import com.spydr.plugin.ui.LogPanel
import com.spydr.plugin.ui.SpydrPanel

/**
 * Factory that creates the SpyDR Agent tool window with two tabs:
 *
 * - **Чат** — main conversation panel.
 * - **Логи** — real-time backend stderr / diagnostic output.
 */
class SpydrToolWindowFactory : ToolWindowFactory {

    override fun createToolWindowContent(project: Project, toolWindow: ToolWindow) {
        val logPanel = LogPanel()
        val spydrPanel = SpydrPanel(project, logPanel)

        val cf = ContentFactory.getInstance()

        val chatContent = cf.createContent(spydrPanel.rootComponent, "Чат", false)
        val logsContent = cf.createContent(logPanel.component, "Логи", false)

        toolWindow.contentManager.addContent(chatContent)
        toolWindow.contentManager.addContent(logsContent)
    }
}
