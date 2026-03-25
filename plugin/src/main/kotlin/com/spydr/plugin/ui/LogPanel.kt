package com.spydr.plugin.ui

import com.intellij.icons.AllIcons
import com.intellij.ui.JBColor
import com.intellij.ui.components.JBLabel
import com.intellij.ui.components.JBScrollPane
import com.intellij.util.ui.JBUI
import com.intellij.util.ui.UIUtil
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
        border = JBUI.Borders.empty(8)
        background = UIUtil.getTextFieldBackground()
    }

    private val scrollPane = JBScrollPane(textPane).apply {
        verticalScrollBarPolicy = JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED
        horizontalScrollBarPolicy = JScrollPane.HORIZONTAL_SCROLLBAR_AS_NEEDED
        border = JBUI.Borders.customLine(JBColor.border(), 1)
    }

    private val autoScrollCheckBox = JCheckBox("Автопрокрутка", true).apply {
        toolTipText = "Автоматически прокручивать лог к новым событиям"
    }

    private val clearButton = JButton("Очистить", AllIcons.Actions.GC).apply {
        addActionListener { clear() }
    }

    val component: JComponent

    init {
        val leftPanel = JPanel(FlowLayout(FlowLayout.LEFT, 6, 0)).apply {
            isOpaque = false
            add(JBLabel("Системные логи"))
            add(clearButton)
        }

        val rightPanel = JPanel(FlowLayout(FlowLayout.RIGHT, 0, 0)).apply {
            isOpaque = false
            add(autoScrollCheckBox)
        }

        val toolbar = JPanel(BorderLayout()).apply {
            border = JBUI.Borders.empty(6, 8)
            add(leftPanel, BorderLayout.WEST)
            add(rightPanel, BorderLayout.EAST)
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
        StyleConstants.setForeground(this, JBColor.namedColor("Label.foreground", JBColor(0x333333, 0xBBBBBB)))
    }

    private val styleWarn = SimpleAttributeSet().apply {
        StyleConstants.setForeground(this, JBColor.namedColor("Label.warningForeground", JBColor(0xCC7700, 0xE5A84B)))
    }

    private val styleError = SimpleAttributeSet().apply {
        StyleConstants.setForeground(this, JBColor.namedColor("Label.errorForeground", JBColor(0xCC0000, 0xFF6B68)))
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
