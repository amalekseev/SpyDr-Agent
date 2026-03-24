package com.spydr.plugin.ui

import com.intellij.icons.AllIcons
import com.intellij.ui.JBColor
import com.intellij.ui.components.JBLabel
import com.intellij.ui.components.JBScrollPane
import com.intellij.ui.components.JBTextArea
import com.intellij.util.ui.JBUI
import com.intellij.util.ui.UIUtil
import java.awt.BorderLayout
import java.awt.Dimension
import java.awt.FlowLayout
import java.awt.event.KeyAdapter
import java.awt.event.KeyEvent
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
    // -----------------------------------------------------------------------
    // Message area
    // -----------------------------------------------------------------------

    private val messagesPanel = JPanel().apply {
        layout = BoxLayout(this, BoxLayout.Y_AXIS)
        border = JBUI.Borders.empty(4)
    }

    private val scrollPane = JBScrollPane(messagesPanel).apply {
        verticalScrollBarPolicy = JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED
        horizontalScrollBarPolicy = JScrollPane.HORIZONTAL_SCROLLBAR_NEVER
        border = JBUI.Borders.empty()
    }

    // -----------------------------------------------------------------------
    // Status line
    // -----------------------------------------------------------------------

    private val statusLabel = JBLabel("").apply {
        foreground = JBColor.GRAY
        border = JBUI.Borders.empty(2, 6)
    }

    // -----------------------------------------------------------------------
    // Input area
    // -----------------------------------------------------------------------

    private val inputArea = JBTextArea(3, 40).apply {
        lineWrap = true
        wrapStyleWord = true
        border = JBUI.Borders.empty(4)
        emptyText.text = "Введите сообщение…"
    }

    private val sendButton = JButton("Отправить").apply {
        addActionListener { doSend() }
    }

    private val stopButton = JButton("Стоп", AllIcons.Actions.Suspend).apply {
        toolTipText = "Остановить текущий запрос"
        isEnabled = false
        addActionListener { onStop() }
    }

    private val clearButton = JButton("Очистить").apply {
        addActionListener { doClear() }
    }

    private val restartButton = JButton("Перезапуск", AllIcons.Actions.Restart).apply {
        toolTipText = "Перезапустить бэкенд"
        addActionListener { onRestart() }
    }

    // -----------------------------------------------------------------------
    // Current streaming state
    // -----------------------------------------------------------------------

    private var currentAssistantBubble: JTextPane? = null
    private var currentAssistantText = StringBuilder()
    private var isBusy = false

    // -----------------------------------------------------------------------
    // Root component
    // -----------------------------------------------------------------------

    val component: JComponent

    init {
        val inputPanel = JPanel(BorderLayout(4, 0)).apply {
            border = JBUI.Borders.empty(4)
            add(JBScrollPane(inputArea).apply {
                preferredSize = Dimension(0, 70)
                border = JBUI.Borders.customLine(JBColor.border(), 1)
            }, BorderLayout.CENTER)

            val buttonsPanel = JPanel(FlowLayout(FlowLayout.RIGHT, 4, 0)).apply {
                add(restartButton)
                add(clearButton)
                add(stopButton)
                add(sendButton)
            }
            add(buttonsPanel, BorderLayout.SOUTH)
        }

        inputArea.addKeyListener(object : KeyAdapter() {
            override fun keyPressed(e: KeyEvent) {
                if (e.keyCode == KeyEvent.VK_ENTER && !e.isShiftDown) {
                    e.consume()
                    doSend()
                }
            }
        })

        component = JPanel(BorderLayout()).apply {
            add(scrollPane, BorderLayout.CENTER)
            add(statusLabel, BorderLayout.NORTH)
            add(inputPanel, BorderLayout.SOUTH)
        }
    }

    // -----------------------------------------------------------------------
    // Public API — called from BackendListener on EDT
    // -----------------------------------------------------------------------

    fun addUserMessage(text: String) {
        val bubble = createBubble(text, isUser = true)
        messagesPanel.add(bubble)
        messagesPanel.add(Box.createVerticalStrut(6))
        scrollToBottom()
    }

    fun beginAssistantMessage() {
        currentAssistantText = StringBuilder()
        val bubble = createBubble("", isUser = false)
        currentAssistantBubble = bubble.getClientProperty("textPane") as? JTextPane
        messagesPanel.add(bubble)
        messagesPanel.add(Box.createVerticalStrut(6))
        scrollToBottom()
    }

    fun appendAssistantText(chunk: String) {
        currentAssistantText.append(chunk)
        currentAssistantBubble?.text = currentAssistantText.toString()
        scrollToBottom()
    }

    fun endAssistantMessage() {
        currentAssistantBubble = null
    }

    fun setStatus(text: String) {
        statusLabel.text = if (text.isNotBlank()) "\u23f3 $text" else ""
    }

    fun clearStatus() {
        statusLabel.text = ""
    }

    fun clearMessages() {
        messagesPanel.removeAll()
        messagesPanel.revalidate()
        messagesPanel.repaint()
        currentAssistantBubble = null
        currentAssistantText = StringBuilder()
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

    private fun createBubble(text: String, isUser: Boolean): JPanel {
        val textPane = JTextPane().apply {
            this.text = text
            isEditable = false
            isOpaque = false
            font = UIUtil.getLabelFont()
            border = JBUI.Borders.empty()
        }

        val panel = JPanel(BorderLayout()).apply {
            border = JBUI.Borders.empty(4, 8)
            isOpaque = true
            background = if (isUser) {
                JBColor(0xE3F2FD, 0x2B3C4F)
            } else {
                JBColor(0xF5F5F5, 0x3C3F41)
            }
            putClientProperty("textPane", textPane)

            val roleLabel = JBLabel(if (isUser) "Вы" else "Агент").apply {
                font = font.deriveFont(java.awt.Font.BOLD)
                border = JBUI.Borders.emptyBottom(2)
            }
            add(roleLabel, BorderLayout.NORTH)
            add(textPane, BorderLayout.CENTER)

            // Prevent stretching in BoxLayout
            maximumSize = Dimension(Int.MAX_VALUE, Int.MAX_VALUE)
        }
        return panel
    }

    private fun scrollToBottom() {
        SwingUtilities.invokeLater {
            messagesPanel.revalidate()
            val vsb = scrollPane.verticalScrollBar
            vsb.value = vsb.maximum
        }
    }
}
