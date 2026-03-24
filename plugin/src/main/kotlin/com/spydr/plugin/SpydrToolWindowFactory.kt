package com.spydr.plugin

import com.intellij.openapi.project.Project
import com.intellij.openapi.wm.ToolWindow
import com.intellij.openapi.wm.ToolWindowFactory
import com.intellij.ui.content.ContentFactory
import com.spydr.plugin.ui.SpydrPanel

/**
 * Factory that creates the SpyDR Agent tool window.
 */
class SpydrToolWindowFactory : ToolWindowFactory {

    override fun createToolWindowContent(project: Project, toolWindow: ToolWindow) {
        val panel = SpydrPanel(project)
        val content = ContentFactory.getInstance().createContent(panel.rootComponent, "", false)
        toolWindow.contentManager.addContent(content)
    }
}
