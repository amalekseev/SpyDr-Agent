package com.spydr.plugin.ui

import com.intellij.ui.JBColor
import com.intellij.ui.components.JBScrollPane
import com.intellij.util.ui.JBUI
import java.awt.BorderLayout
import java.awt.FlowLayout
import java.awt.Font
import java.text.SimpleDateFormat
import java.util.*
import javax.swing.*
import javax.swing.text.SimpleAttributeSet
import javax.swing.text.StyleConstants

/**
 * Console-style log panel that displays backend stderr and lifecycle
 * events in real time.  Lives in a separate tool window tab ("Логи")
 * so it never clutters the chat.
 */
class LogPanel {

    private val textPane = JTextPane().apply {
        isEditable = false
        font = Font(Font.MONOSPACED, Font.PLAIN, 12)
        border = JBUI.Borders.empty(4)
    }

    private val scrollPane = JBScrollPane(textPane).apply {
        verticalScrollBarPolicy = JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED
        horizontalScrollBarPolicy = JScrollPane.HORIZONTAL_SCROLLBAR_AS_NEEDED
        border = JBUI.Borders.empty()
    }

    private val autoScrollCheckBox = JCheckBox("Автопрокрутка", true)

    private val clearButton = JButton("Очистить").apply {
        addActionListener { clear() }
    }

    val component: JComponent

    init {
        val toolbar = JPanel(FlowLayout(FlowLayout.LEFT, 4, 2)).apply {
            add(autoScrollCheckBox)
            add(clearButton)
        }

        component = JPanel(BorderLayout()).apply {
            add(toolbar, BorderLayout.NORTH)
            add(scrollPane, BorderLayout.CENTER)
        }
    }

    // -- Styles ---------------------------------------------------------------

    private val styleTimestamp = SimpleAttributeSet().apply {
        StyleConstants.setForeground(this, JBColor.GRAY)
        StyleConstants.setFontSize(this, 11)
    }

    private val styleInfo = SimpleAttributeSet().apply {
        StyleConstants.setForeground(this, JBColor(0x333333, 0xBBBBBB))
    }

    private val styleWarn = SimpleAttributeSet().apply {
        StyleConstants.setForeground(this, JBColor(0xCC7700, 0xE5A84B))
    }

    private val styleError = SimpleAttributeSet().apply {
        StyleConstants.setForeground(this, JBColor(0xCC0000, 0xFF6B68))
        StyleConstants.setBold(this, true)
    }

    private val styleStderr = SimpleAttributeSet().apply {
        StyleConstants.setForeground(this, JBColor(0x993333, 0xCF6679))
    }

    private val timeFmt = SimpleDateFormat("HH:mm:ss.SSS")

    // -- Public API -----------------------------------------------------------

    enum class Level { INFO, WARN, ERROR, STDERR }

    /** Append a log line (thread-safe — dispatches to EDT). */
    fun append(text: String, level: Level = Level.INFO) {
        SwingUtilities.invokeLater {
            val doc = textPane.styledDocument
            val ts = timeFmt.format(Date())

            val style = when (level) {
                Level.INFO -> styleInfo
                Level.WARN -> styleWarn
                Level.ERROR -> styleError
                Level.STDERR -> styleStderr
            }

            val prefix = when (level) {
                Level.INFO -> "INFO "
                Level.WARN -> "WARN "
                Level.ERROR -> "ERROR"
                Level.STDERR -> "PY   "
            }

            doc.insertString(doc.length, "[$ts] ", styleTimestamp)
            doc.insertString(doc.length, "$prefix  $text\n", style)

            if (autoScrollCheckBox.isSelected) {
                textPane.caretPosition = doc.length
            }
        }
    }

    fun clear() {
        SwingUtilities.invokeLater {
            textPane.text = ""
        }
    }
}
