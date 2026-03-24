package com.spydr.plugin.settings

import com.intellij.openapi.fileChooser.FileChooserDescriptorFactory
import com.intellij.openapi.options.Configurable
import com.intellij.openapi.ui.TextFieldWithBrowseButton
import com.intellij.ui.components.JBLabel
import com.intellij.ui.components.JBTextField
import com.intellij.util.ui.JBUI
import java.awt.GridBagConstraints
import java.awt.GridBagLayout
import javax.swing.JComponent
import javax.swing.JPanel

/**
 * Settings page under **File → Settings → Tools → SpyDR Agent**.
 *
 * Fields:
 * - **Python** – path to the interpreter. Leave empty for automatic
 *   setup (recommended for new users).
 * - **.env файл** – path to a `.env` file with API keys.
 * - **Feature директория** – default directory for generated `.feature` files.
 */
class SpydrSettingsConfigurable : Configurable {

    private var pythonField: TextFieldWithBrowseButton? = null
    private var featureDirField: TextFieldWithBrowseButton? = null
    private var envFileField: TextFieldWithBrowseButton? = null

    override fun getDisplayName(): String = "SpyDR Agent"

    override fun createComponent(): JComponent {
        val pyField = TextFieldWithBrowseButton(JBTextField()).apply {
            addBrowseFolderListener(
                "Выберите Python интерпретатор",
                null,
                null,
                FileChooserDescriptorFactory.createSingleFileDescriptor(),
            )
        }
        pythonField = pyField

        val envField = TextFieldWithBrowseButton(JBTextField()).apply {
            addBrowseFolderListener(
                "Выберите .env файл",
                null,
                null,
                FileChooserDescriptorFactory.createSingleFileDescriptor(),
            )
        }
        envFileField = envField

        val fDirField = TextFieldWithBrowseButton(JBTextField()).apply {
            addBrowseFolderListener(
                "Выберите директорию для .feature файлов",
                null,
                null,
                FileChooserDescriptorFactory.createSingleFolderDescriptor(),
            )
        }
        featureDirField = fDirField

        val hintColor = JBUI.CurrentTheme.ContextHelp.FOREGROUND

        val panel = JPanel(GridBagLayout()).apply {
            border = JBUI.Borders.empty(8)

            val gbc = GridBagConstraints().apply {
                fill = GridBagConstraints.HORIZONTAL
                insets = JBUI.insets(4, 4)
            }

            // Row 0: Python path
            gbc.gridy = 0; gbc.gridx = 0; gbc.weightx = 0.0
            add(JBLabel("Python:"), gbc)
            gbc.gridx = 1; gbc.weightx = 1.0
            add(pyField, gbc)

            // Row 1: hint
            gbc.gridy = 1; gbc.gridx = 1; gbc.weightx = 1.0
            add(JBLabel("<html><small>Оставьте пустым — плагин сам найдёт Python и создаст venv</small></html>").apply {
                foreground = hintColor
            }, gbc)

            // Row 2: .env file
            gbc.gridy = 2; gbc.gridx = 0; gbc.weightx = 0.0
            add(JBLabel(".env файл:"), gbc)
            gbc.gridx = 1; gbc.weightx = 1.0
            add(envField, gbc)

            // Row 3: hint
            gbc.gridy = 3; gbc.gridx = 1; gbc.weightx = 1.0
            add(JBLabel("<html><small>Файл с API-ключами (GIGACHAT_*, CONNECTION_STRING и т.д.)</small></html>").apply {
                foreground = hintColor
            }, gbc)

            // Row 4: Default feature dir
            gbc.gridy = 4; gbc.gridx = 0; gbc.weightx = 0.0
            add(JBLabel("Feature директория:"), gbc)
            gbc.gridx = 1; gbc.weightx = 1.0
            add(fDirField, gbc)

            // Spacer
            gbc.gridy = 5; gbc.gridx = 0; gbc.weighty = 1.0; gbc.gridwidth = 2
            add(JPanel(), gbc)
        }

        reset()
        return panel
    }

    override fun isModified(): Boolean {
        val s = SpydrSettingsState.getInstance()
        return pythonField?.text != s.pythonPath ||
                featureDirField?.text != s.defaultFeatureDir ||
                envFileField?.text != s.envFilePath
    }

    override fun apply() {
        val s = SpydrSettingsState.getInstance()
        s.pythonPath = pythonField?.text ?: ""
        s.defaultFeatureDir = featureDirField?.text ?: ""
        s.envFilePath = envFileField?.text ?: ""
    }

    override fun reset() {
        val s = SpydrSettingsState.getInstance()
        pythonField?.text = s.pythonPath
        featureDirField?.text = s.defaultFeatureDir
        envFileField?.text = s.envFilePath
    }

    override fun disposeUIResources() {
        pythonField = null
        featureDirField = null
        envFileField = null
    }
}
