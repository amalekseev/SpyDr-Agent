package com.spydr.plugin.ui

import com.intellij.icons.AllIcons
import com.intellij.ui.ColorUtil
import com.intellij.ui.JBColor
import com.intellij.ui.jcef.JBCefApp
import com.intellij.ui.jcef.JBCefBrowser
import com.intellij.ui.components.JBLabel
import com.intellij.ui.components.JBScrollPane
import com.intellij.ui.components.JBTextArea
import com.intellij.util.ui.JBUI
import com.intellij.util.ui.UIUtil
import java.awt.BorderLayout
import java.awt.Color
import java.awt.Dimension
import java.awt.FlowLayout
import java.awt.Graphics
import java.awt.Graphics2D
import java.awt.RenderingHints
import java.awt.event.KeyAdapter
import java.awt.event.KeyEvent
import java.awt.event.FocusAdapter
import java.awt.event.FocusEvent
import javax.swing.BorderFactory
import javax.swing.*

/**
 * Chat panel with message history, status line, input area,
 * and **Stop / Restart** controls.
 */
class ChatPanel(
    private val onSend: (String) -> Unit,
    private val onClear: () -> Unit,
    private val onStop: () -> Unit,
    private val onRestart: () -> Unit,
) {
    private enum class MessageRole { USER, ASSISTANT }
    private data class ChatMessage(val role: MessageRole, var text: String)

    // -----------------------------------------------------------------------
    // Message area
    // -----------------------------------------------------------------------

    private val conversation = mutableListOf<ChatMessage>()
    private var currentAssistantIndex: Int? = null
    private var currentAssistantText = StringBuilder()
    private var inputFocused = false

    private val jcefBrowser: JBCefBrowser? = if (JBCefApp.isSupported()) JBCefBrowser() else null

    private val messagesPanel = JPanel().apply {
        layout = BoxLayout(this, BoxLayout.Y_AXIS)
        border = JBUI.Borders.empty(4)
    }

    private val scrollPane = JBScrollPane(messagesPanel).apply {
        verticalScrollBarPolicy = JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED
        horizontalScrollBarPolicy = JScrollPane.HORIZONTAL_SCROLLBAR_NEVER
        border = JBUI.Borders.empty()
    }

    private val conversationComponent: JComponent = jcefBrowser?.component ?: scrollPane

    // -----------------------------------------------------------------------
    // Status line
    // -----------------------------------------------------------------------

    private val statusLabel = JBLabel("").apply {
        foreground = JBColor.namedColor("Label.infoForeground", JBColor.GRAY)
        border = JBUI.Borders.empty(6, 8, 4, 8)
    }

    // -----------------------------------------------------------------------
    // Input area
    // -----------------------------------------------------------------------

    private val inputArea = JBTextArea(3, 40).apply {
        lineWrap = true
        wrapStyleWord = true
        border = JBUI.Borders.empty(6, 8)
        emptyText.text = "Введите сообщение…"
    }

    private val sendButton = JButton("Отправить", AllIcons.Actions.Execute).apply {
        toolTipText = "Отправить сообщение (Enter)"
        addActionListener { doSend() }
    }

    private val stopButton = JButton("Стоп", AllIcons.Actions.Suspend).apply {
        toolTipText = "Остановить текущий запрос"
        isEnabled = false
        addActionListener { onStop() }
    }

    private val clearButton = JButton("Очистить", AllIcons.Actions.GC).apply {
        addActionListener { doClear() }
    }

    private val restartButton = JButton("Перезапуск", AllIcons.Actions.Restart).apply {
        toolTipText = "Перезапустить бэкенд"
        addActionListener { onRestart() }
    }

    // -----------------------------------------------------------------------
    // Current streaming state
    // -----------------------------------------------------------------------
    private var isBusy = false

    // -----------------------------------------------------------------------
    // Root component
    // -----------------------------------------------------------------------

    val component: JComponent

    init {
        val inputScroll = JBScrollPane(inputArea).apply {
            preferredSize = Dimension(0, 78)
            border = JBUI.Borders.empty()
            isOpaque = false
            viewport.isOpaque = false
            background = inputCardBackground()
            viewport.background = inputCardBackground()
        }

        inputArea.isOpaque = false

        val inputCard = object : JPanel(BorderLayout()) {
            override fun paintComponent(g: Graphics) {
                val g2 = g.create() as Graphics2D
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)

                val arc = JBUI.scale(12)
                val inset = JBUI.scale(1)
                val w = width - inset * 2
                val h = height - inset * 2

                g2.color = inputCardBackground()
                g2.fillRoundRect(inset, inset, w, h, arc, arc)

                g2.color = if (inputFocused) inputCardFocusedBorderColor() else inputCardBorderColor()
                g2.drawRoundRect(inset, inset, w, h, arc, arc)
                g2.dispose()
            }
        }.apply {
            border = JBUI.Borders.empty(5, 7)
            isOpaque = false
            add(inputScroll, BorderLayout.CENTER)
        }

        val inputCardShell = JPanel(BorderLayout()).apply {
            border = JBUI.Borders.empty(0)
            isOpaque = true
            background = inputPanelBackdrop()
            add(inputCard, BorderLayout.CENTER)
        }

        val secondaryActions = JPanel(FlowLayout(FlowLayout.LEFT, 6, 0)).apply {
            isOpaque = false
            add(restartButton)
            add(clearButton)
            add(stopButton)
        }

        val primaryActions = JPanel(FlowLayout(FlowLayout.RIGHT, 0, 0)).apply {
            isOpaque = false
            add(sendButton)
        }

        val actionsPanel = JPanel(BorderLayout()).apply {
            isOpaque = false
            border = JBUI.Borders.empty(6, 0, 0, 0)
            add(secondaryActions, BorderLayout.WEST)
            add(primaryActions, BorderLayout.EAST)
        }

        val inputPanel = JPanel(BorderLayout()).apply {
            border = JBUI.Borders.empty(6, 8, 8, 8)
            isOpaque = false
            add(inputCardShell, BorderLayout.CENTER)
            add(actionsPanel, BorderLayout.SOUTH)
        }

        inputArea.addKeyListener(object : KeyAdapter() {
            override fun keyPressed(e: KeyEvent) {
                if (e.keyCode == KeyEvent.VK_ENTER && !e.isShiftDown) {
                    e.consume()
                    doSend()
                }
            }
        })

        inputArea.addFocusListener(object : FocusAdapter() {
            override fun focusGained(e: FocusEvent?) {
                inputFocused = true
                inputCard.repaint()
            }

            override fun focusLost(e: FocusEvent?) {
                inputFocused = false
                inputCard.repaint()
            }
        })

        component = JPanel(BorderLayout()).apply {
            add(conversationComponent, BorderLayout.CENTER)
            add(statusLabel, BorderLayout.NORTH)
            add(inputPanel, BorderLayout.SOUTH)
        }
        renderConversation()
    }

    // -----------------------------------------------------------------------
    // Public API — called from BackendListener on EDT
    // -----------------------------------------------------------------------

    fun addUserMessage(text: String) {
        conversation.add(ChatMessage(MessageRole.USER, text))
        renderConversation()
    }

    fun beginAssistantMessage() {
        currentAssistantText = StringBuilder()
        conversation.add(ChatMessage(MessageRole.ASSISTANT, ""))
        currentAssistantIndex = conversation.lastIndex
        renderConversation()
    }

    fun appendAssistantText(chunk: String) {
        currentAssistantText.append(chunk)
        val idx = currentAssistantIndex ?: return
        if (idx in conversation.indices) {
            conversation[idx].text = currentAssistantText.toString()
            renderConversation()
        }
    }

    fun endAssistantMessage() {
        currentAssistantIndex = null
    }

    fun setStatus(text: String) {
        statusLabel.text = if (text.isNotBlank()) "\u23f3  $text" else ""
    }

    fun clearStatus() {
        statusLabel.text = ""
    }

    fun clearMessages() {
        conversation.clear()
        currentAssistantIndex = null
        messagesPanel.removeAll()
        messagesPanel.revalidate()
        messagesPanel.repaint()
        currentAssistantText = StringBuilder()
        renderConversation()
    }

    fun setBusy(busy: Boolean) {
        isBusy = busy
        sendButton.isEnabled = !busy
        stopButton.isEnabled = busy
        inputArea.isEditable = !busy
    }

    // -----------------------------------------------------------------------
    // Internal
    // -----------------------------------------------------------------------

    private fun doSend() {
        if (isBusy) return
        val text = inputArea.text.trim()
        if (text.isEmpty()) return
        inputArea.text = ""
        onSend(text)
    }

    private fun doClear() {
        onClear()
    }

    private fun renderConversation() {
        if (jcefBrowser != null) {
            jcefBrowser.loadHTML(buildJcefConversationHtml())
            scrollToBottom()
            return
        }

        messagesPanel.removeAll()
        conversation.forEach { msg ->
            val row = createMessageRow(msg.text, msg.role)
            messagesPanel.add(row)
            messagesPanel.add(Box.createVerticalStrut(6))
        }
        messagesPanel.revalidate()
        messagesPanel.repaint()
        scrollToBottom()
    }

    private fun buildJcefConversationHtml(): String {
        val fg = ColorUtil.toHex(UIUtil.getLabelForeground())
        val bg = ColorUtil.toHex(UIUtil.getPanelBackground())
        val border = ColorUtil.toHex(lightBorderColor())
        val accent = ColorUtil.toHex(
            JBColor.namedColor("Component.accentColor", JBColor(0x3574F0, 0x548AF7))
        )
        val muted = ColorUtil.toHex(JBColor.namedColor("Label.infoForeground", JBColor.GRAY))
        val userBg = ColorUtil.toHex(
            ColorUtil.mix(UIUtil.getPanelBackground(), JBColor(0x3574F0, 0x548AF7), 0.07)
        )
        val assistantBg = ColorUtil.toHex(
            ColorUtil.mix(UIUtil.getPanelBackground(), UIUtil.getTextFieldBackground(), 0.72)
        )
        val cardShadow = ColorUtil.toHex(ColorUtil.mix(JBColor(0x000000, 0xFFFFFF), UIUtil.getPanelBackground(), 0.92))
        val cardHoverShadow = ColorUtil.toHex(
            ColorUtil.mix(JBColor(0x000000, 0xFFFFFF), UIUtil.getPanelBackground(), 0.86)
        )
        val hoverBorder = ColorUtil.toHex(ColorUtil.mix(lightBorderColor(), JBColor(0x3574F0, 0x548AF7), 0.15))

        val messagesHtml = conversation.joinToString(separator = "") { msg ->
            val isUser = msg.role == MessageRole.USER
            val role = if (isUser) "Вы" else "Агент"
            val alignment = if (isUser) "justify-content:flex-end;" else "justify-content:flex-start;"
            val bubbleBg = if (isUser) userBg else assistantBg
            val body = if (isUser) userTextToHtmlBody(msg.text) else markdownToHtmlBody(msg.text)
            val roleDot = if (isUser) accent else muted

            """
            <div style="$alignment display:flex; margin:0 0 10px 0;">
              <div class="chatCard" style="max-width:min(78%, 760px); border:1px solid #$border; background:#$bubbleBg; border-radius:12px; box-shadow:0 1px 0 #$cardShadow; overflow:hidden;">
                <div style="display:flex; align-items:center; gap:6px; padding:7px 10px; border-bottom:1px solid #$border; font-weight:600; font-size:11px; letter-spacing:0.2px; color:#$muted;">
                  <span style="display:inline-block; width:7px; height:7px; border-radius:50%; background:#$roleDot;"></span>
                  <span>$role</span>
                </div>
                <div style="padding:9px 10px 8px 10px;">$body</div>
              </div>
            </div>
            """.trimIndent()
        }

        return """
            <html>
            <head>
              <style>
                .chatCard {
                  transition: border-color 120ms ease, box-shadow 120ms ease, transform 120ms ease;
                }
                .chatCard:hover {
                  border-color: #$hoverBorder !important;
                  box-shadow: 0 2px 0 #$cardHoverShadow;
                  transform: translateY(-1px);
                }
              </style>
            </head>
            <body style="margin:0; padding:4px; color:#$fg; background:#$bg; font-family:Sans-Serif; font-size:12px; line-height:1.35;">
              <div style="max-width:980px; margin:0 auto;">$messagesHtml</div>
              <script>window.scrollTo(0, document.body.scrollHeight);</script>
            </body>
            </html>
        """.trimIndent()
    }

    private fun createMessageRow(rawText: String, role: MessageRole): JPanel {
        val isUser = role == MessageRole.USER
        val messageEditor = JEditorPane("text/html", "").apply {
            isEditable = false
            isOpaque = false
            border = JBUI.Borders.empty()
            putClientProperty(JEditorPane.HONOR_DISPLAY_PROPERTIES, true)
            this.text = if (isUser) userTextToHtml(rawText) else markdownToHtml(rawText)
        }

        val bubblePanel = JPanel(BorderLayout()).apply {
            border = JBUI.Borders.empty(6, 8)
            isOpaque = true
            background = bubbleBackground(isUser)
            this.border = BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(lightBorderColor(), 1, true),
                JBUI.Borders.empty(6, 8)
            )
            putClientProperty("messageEditor", messageEditor)

            val roleLabel = JBLabel(if (isUser) "Вы" else "Агент").apply {
                font = font.deriveFont(java.awt.Font.BOLD)
                border = JBUI.Borders.emptyBottom(2)
            }
            add(roleLabel, BorderLayout.NORTH)
            add(messageEditor, BorderLayout.CENTER)

            maximumSize = Dimension(520, Int.MAX_VALUE)
        }

        return JPanel(BorderLayout()).apply {
            isOpaque = false
            border = JBUI.Borders.empty(0, 4)
            if (isUser) {
                add(bubblePanel, BorderLayout.EAST)
            } else {
                add(bubblePanel, BorderLayout.WEST)
            }
            putClientProperty("messageEditor", messageEditor)
        }
    }

    private fun bubbleBackground(isUser: Boolean): Color {
        val panel = UIUtil.getPanelBackground()
        val accent = JBColor.namedColor("Component.accentColor", JBColor(0x3574F0, 0x548AF7))
        return if (isUser) {
            ColorUtil.mix(panel, accent, 0.07)
        } else {
            ColorUtil.mix(panel, UIUtil.getTextFieldBackground(), 0.72)
        }
    }

    private fun lightBorderColor(): Color {
        return ColorUtil.mix(JBColor.border(), UIUtil.getPanelBackground(), 0.66)
    }

    private fun matteInputBackground(): Color {
        return ColorUtil.mix(UIUtil.getPanelBackground(), UIUtil.getTextFieldBackground(), 0.76)
    }

    private fun inputCardBackground(): Color {
        return ColorUtil.mix(UIUtil.getPanelBackground(), Color.WHITE, 0.18)
    }

    private fun inputCardBorderColor(): Color {
        return Color.WHITE
    }

    private fun inputCardFocusedBorderColor(): Color {
        return Color.WHITE
    }

    private fun inputPanelBackdrop(): Color {
        return ColorUtil.mix(UIUtil.getPanelBackground(), Color.WHITE, 0.08)
    }

    private fun userTextToHtml(text: String): String {
        return wrapHtml(userTextToHtmlBody(text))
    }

    private fun userTextToHtmlBody(text: String): String {
        val escaped = escapeHtml(text).replace("\n", "<br/>")
        return "<p style='margin:0 0 6px 0;'>$escaped</p>"
    }

    private fun markdownToHtml(markdown: String): String = wrapHtml(markdownToHtmlBody(markdown))

    private fun markdownToHtmlBody(markdown: String): String {
        val lines = markdown.replace("\r\n", "\n").split('\n')
        val body = StringBuilder()
        var inCodeBlock = false
        var inList = false
        val muted = ColorUtil.toHex(JBColor.namedColor("Label.infoForeground", JBColor.GRAY))
        val codeBg = ColorUtil.toHex(
            ColorUtil.mix(UIUtil.getPanelBackground(), UIUtil.getTextFieldBackground(), 0.6)
        )

        for (line in lines) {
            val trimmed = line.trim()

            if (trimmed.startsWith("```")) {
                if (!inCodeBlock) {
                    if (inList) {
                        body.append("</ul>")
                        inList = false
                    }
                    body.append(
                        "<pre style='background:#$codeBg; padding:8px; margin:2px 0 8px 0;'>" +
                            "<code style='font-family:Monospaced;'>"
                    )
                    inCodeBlock = true
                } else {
                    body.append("</code></pre>")
                    inCodeBlock = false
                }
                continue
            }

            if (inCodeBlock) {
                body.append(escapeHtml(line)).append('\n')
                continue
            }

            val headingLevel = headingLevel(trimmed)
            if (headingLevel > 0) {
                if (inList) {
                    body.append("</ul>")
                    inList = false
                }
                val title = trimmed.substring(headingLevel).trimStart()
                val headingStyle = when (headingLevel) {
                    1 -> "margin:4px 0 6px 0; font-size:14px;"
                    2 -> "margin:4px 0 6px 0; font-size:13px;"
                    else -> "margin:4px 0 6px 0; font-size:12px; color:#$muted;"
                }
                body.append("<h").append(headingLevel).append(" style='").append(headingStyle).append("'>")
                    .append(applyInlineMarkdown(title, codeBg))
                    .append("</h").append(headingLevel).append(">")
                continue
            }

            val isListItem = trimmed.startsWith("- ") || trimmed.startsWith("* ")
            if (isListItem) {
                if (!inList) {
                    body.append("<ul style='margin:0 0 6px 0; padding-left:16px;'>")
                    inList = true
                }
                body.append("<li style='margin:2px 0;'>")
                    .append(applyInlineMarkdown(trimmed.substring(2).trimStart(), codeBg))
                    .append("</li>")
                continue
            }

            if (trimmed.isBlank()) {
                if (inList) {
                    body.append("</ul>")
                    inList = false
                }
                body.append("<div style='height:4px;'></div>")
                continue
            }

            if (inList) {
                body.append("</ul>")
                inList = false
            }
            body.append("<p style='margin:0 0 6px 0;'>")
                .append(applyInlineMarkdown(trimmed, codeBg))
                .append("</p>")
        }

        if (inList) {
            body.append("</ul>")
        }
        if (inCodeBlock) {
            body.append("</code></pre>")
        }

        return body.toString()
    }

    private fun headingLevel(line: String): Int {
        var idx = 0
        while (idx < line.length && line[idx] == '#') {
            idx++
        }
        return if (idx in 1..3 && idx < line.length && line[idx] == ' ') idx else 0
    }

    private fun applyInlineMarkdown(text: String, codeBg: String): String {
        var value = escapeHtml(text)
        value = value.replace(
            Regex("`([^`]+)`"),
            "<code style='background:#$codeBg; padding:1px 4px; font-family:Monospaced;'>$1</code>"
        )
        value = value.replace(Regex("\\*\\*([^*]+)\\*\\*"), "<b>$1</b>")
        value = value.replace(Regex("\\*([^*]+)\\*"), "<i>$1</i>")
        return value
    }

    private fun wrapHtml(content: String): String {
        val fg = ColorUtil.toHex(UIUtil.getLabelForeground())
        return """
            <html>
            <body style="margin:0; color:#$fg; font-family:Sans-Serif; font-size:12px; line-height:1.35;">
              $content
            </body>
            </html>
        """.trimIndent()
    }

    private fun escapeHtml(text: String): String = buildString(text.length) {
        text.forEach { ch ->
            when (ch) {
                '&' -> append("&amp;")
                '<' -> append("&lt;")
                '>' -> append("&gt;")
                '"' -> append("&quot;")
                '\'' -> append("&#39;")
                else -> append(ch)
            }
        }
    }

    private fun scrollToBottom() {
        if (jcefBrowser != null) {
            jcefBrowser.cefBrowser.executeJavaScript(
                "window.scrollTo(0, document.body.scrollHeight);",
                jcefBrowser.cefBrowser.url,
                0
            )
            return
        }
        SwingUtilities.invokeLater {
            messagesPanel.revalidate()
            val vsb = scrollPane.verticalScrollBar
            vsb.value = vsb.maximum
        }
    }
}
