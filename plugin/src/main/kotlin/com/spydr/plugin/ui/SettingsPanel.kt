package com.spydr.plugin.ui

import com.intellij.openapi.fileChooser.FileChooserDescriptorFactory
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.TextFieldWithBrowseButton
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
            border = JBUI.Borders.empty(6, 8)

            val gbc = GridBagConstraints().apply {
                fill = GridBagConstraints.HORIZONTAL
                insets = JBUI.insets(2, 4)
            }

            // Row 0: Project
            gbc.gridy = 0; gbc.gridx = 0; gbc.weightx = 0.0
            add(JBLabel("Проект:"), gbc)
            gbc.gridx = 1; gbc.weightx = 1.0; gbc.gridwidth = 2
            add(projectCombo, gbc)
            gbc.gridwidth = 1

            // Row 1: Feature file
            gbc.gridy = 1; gbc.gridx = 0; gbc.weightx = 0.0
            add(JBLabel("Feature файл:"), gbc)
            gbc.gridx = 1; gbc.weightx = 1.0; gbc.gridwidth = 2
            add(featureFileField, gbc)
            gbc.gridwidth = 1

            // Row 2: Validation
            gbc.gridy = 2; gbc.gridx = 0; gbc.weightx = 0.0
            add(validationCheckbox, gbc)
            gbc.gridx = 1; gbc.weightx = 0.0
            add(JBLabel("Макс. итераций:"), gbc)
            gbc.gridx = 2; gbc.weightx = 0.3
            add(maxIterationsSpinner, gbc)
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
