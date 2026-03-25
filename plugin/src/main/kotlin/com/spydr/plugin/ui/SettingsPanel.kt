package com.spydr.plugin.ui

import com.intellij.openapi.fileChooser.FileChooserDescriptorFactory
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.TextFieldWithBrowseButton
import com.intellij.ui.JBColor
import com.intellij.ui.TitledSeparator
import com.intellij.ui.components.JBCheckBox
import com.intellij.ui.components.JBLabel
import com.intellij.util.ui.JBUI
import java.awt.GridBagConstraints
import java.awt.GridBagLayout
import javax.swing.DefaultComboBoxModel
import javax.swing.JComboBox
import javax.swing.JPanel
import javax.swing.JSpinner
import javax.swing.SpinnerNumberModel

/**
 * Top panel with settings: project selector, feature file path,
 * validation toggle and max iterations.
 */
class SettingsPanel(private val project: Project) {

    // -----------------------------------------------------------------------
    // Project selector
    // -----------------------------------------------------------------------

    private val projectModel = DefaultComboBoxModel<String>()
    val projectCombo = JComboBox(projectModel).apply {
        toolTipText = "Выбрать проект"
    }

    // -----------------------------------------------------------------------
    // Feature file path
    // -----------------------------------------------------------------------

    val featureFileField = TextFieldWithBrowseButton().apply {
        val descriptor = FileChooserDescriptorFactory.createSingleFileDescriptor("feature")
        addBrowseFolderListener("Выберите .feature файл", null, project, descriptor)
        toolTipText = "Путь к целевому .feature файлу"
    }

    // -----------------------------------------------------------------------
    // Validation
    // -----------------------------------------------------------------------

    val validationCheckbox = JBCheckBox("Валидация feature", false)

    val maxIterationsSpinner = JSpinner(SpinnerNumberModel(3, 1, 10, 1)).apply {
        isEnabled = false
        toolTipText = "Макс. итераций валидации"
    }

    // -----------------------------------------------------------------------
    // Component
    // -----------------------------------------------------------------------

    val component: JPanel

    init {
        validationCheckbox.addChangeListener {
            maxIterationsSpinner.isEnabled = validationCheckbox.isSelected
        }

        component = JPanel(GridBagLayout()).apply {
            border = JBUI.Borders.empty(8, 8, 6, 8)

            val gbc = GridBagConstraints().apply {
                fill = GridBagConstraints.HORIZONTAL
                insets = JBUI.insets(3, 4)
                anchor = GridBagConstraints.WEST
            }

            // Header
            gbc.gridy = 0; gbc.gridx = 0; gbc.weightx = 1.0; gbc.gridwidth = 3
            add(TitledSeparator("Контекст генерации"), gbc)

            gbc.gridy = 1; gbc.gridx = 0; gbc.weightx = 1.0; gbc.gridwidth = 3
            add(JBLabel("Эти параметры применяются к текущему сообщению в чате.").apply {
                foreground = JBColor.namedColor("Label.infoForeground", JBColor.GRAY)
                border = JBUI.Borders.emptyBottom(2)
            }, gbc)
            gbc.gridwidth = 1

            // Row 0: Project
            gbc.gridy = 2; gbc.gridx = 0; gbc.weightx = 0.0
            add(JBLabel("Проект:"), gbc)
            gbc.gridx = 1; gbc.weightx = 1.0; gbc.gridwidth = 2
            add(projectCombo, gbc)
            gbc.gridwidth = 1

            // Row 1: Feature file
            gbc.gridy = 3; gbc.gridx = 0; gbc.weightx = 0.0
            add(JBLabel("Feature файл:"), gbc)
            gbc.gridx = 1; gbc.weightx = 1.0; gbc.gridwidth = 2
            add(featureFileField, gbc)
            gbc.gridwidth = 1

            // Validation header
            gbc.gridy = 4; gbc.gridx = 0; gbc.weightx = 1.0; gbc.gridwidth = 3
            gbc.insets = JBUI.insets(8, 4, 2, 4)
            add(TitledSeparator("Валидация"), gbc)
            gbc.gridwidth = 1
            gbc.insets = JBUI.insets(3, 4)

            // Row 2: Validation
            gbc.gridy = 5; gbc.gridx = 0; gbc.weightx = 0.0
            add(validationCheckbox, gbc)
            gbc.gridx = 1; gbc.weightx = 0.0
            add(JBLabel("Макс. итераций:"), gbc)
            gbc.gridx = 2; gbc.weightx = 0.3
            add(maxIterationsSpinner, gbc)

            gbc.gridy = 6; gbc.gridx = 0; gbc.weightx = 1.0; gbc.gridwidth = 3
            add(JBLabel("При выключенной валидации используется одна генерация без повторных попыток.").apply {
                foreground = JBColor.namedColor("Label.disabledForeground", JBColor.GRAY)
                border = JBUI.Borders.emptyTop(1)
            }, gbc)
        }
    }

    // -----------------------------------------------------------------------
    // Public API
    // -----------------------------------------------------------------------

    val selectedProject: String
        get() {
            val sel = projectCombo.selectedItem as? String ?: ""
            return if (sel == NO_PROJECT) "" else sel
        }

    val featureFilePath: String
        get() = featureFileField.text.trim()

    val validationEnabled: Boolean
        get() = validationCheckbox.isSelected

    val maxValidationIterations: Int
        get() = maxIterationsSpinner.value as Int

    fun setProjects(projects: List<String>) {
        projectModel.removeAllElements()
        projectModel.addElement(NO_PROJECT)
        projects.forEach { projectModel.addElement(it) }
    }

    companion object {
        private const val NO_PROJECT = "(без проекта)"
    }
}
