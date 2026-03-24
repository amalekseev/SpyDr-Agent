package com.spydr.plugin.settings

import com.intellij.openapi.fileChooser.FileChooserDescriptorFactory
import com.intellij.openapi.options.Configurable
import com.intellij.openapi.ui.ComboBox
import com.intellij.openapi.ui.TextFieldWithBrowseButton
import com.intellij.ui.TitledSeparator
import com.intellij.ui.components.JBCheckBox
import com.intellij.ui.components.JBLabel
import com.intellij.ui.components.JBScrollPane
import com.intellij.ui.components.JBTextField
import com.intellij.util.ui.FormBuilder
import com.intellij.util.ui.JBUI
import javax.swing.DefaultComboBoxModel
import javax.swing.JComponent
import javax.swing.JSpinner
import javax.swing.SpinnerNumberModel

/**
 * Settings page: **File → Settings → Tools → SpyDR Agent**.
 *
 * Contains all the configuration that was previously spread across
 * `src/agents/config.yml` and `src/configs/config.yml`.
 */
class SpydrSettingsConfigurable : Configurable {

    // ---- Environment ----------------------------------------------------
    private var pythonField: TextFieldWithBrowseButton? = null
    private var envFileField: TextFieldWithBrowseButton? = null
    private var featureDirField: TextFieldWithBrowseButton? = null

    // ---- Main LLM -------------------------------------------------------
    private var llmProviderCombo: ComboBox<String>? = null
    private var llmModelField: JBTextField? = null
    private var llmTempSpinner: JSpinner? = null

    // ---- Validation -----------------------------------------------------
    private var valMaxIterSpinner: JSpinner? = null
    private var valSameLlmCheckbox: JBCheckBox? = null
    private var valProviderCombo: ComboBox<String>? = null
    private var valModelField: JBTextField? = null
    private var valTempSpinner: JSpinner? = null

    // ---- Embeddings -----------------------------------------------------
    private var embProviderCombo: ComboBox<String>? = null
    private var embModelField: JBTextField? = null

    // ---- RAG: Steps -----------------------------------------------------
    private var stepsCollectionField: JBTextField? = null
    private var stepsTopKSpinner: JSpinner? = null

    // ---- RAG: Docs ------------------------------------------------------
    private var docsCollectionField: JBTextField? = null
    private var docsPathField: JBTextField? = null
    private var docsTopKSpinner: JSpinner? = null
    private var docsChunkSizeSpinner: JSpinner? = null
    private var docsChunkOverlapSpinner: JSpinner? = null

    // ---- RAG: Few Shots -------------------------------------------------
    private var fewShotsCollectionField: JBTextField? = null
    private var fewShotsTopKSpinner: JSpinner? = null
    private var fewShotsIndexField: JBTextField? = null
    private var fewShotsDirField: JBTextField? = null
    private var fewShotsBatchSizeSpinner: JSpinner? = null

    // ---- Docstring ------------------------------------------------------
    private var docstringLangsField: JBTextField? = null

    override fun getDisplayName(): String = "SpyDR Agent"

    // =====================================================================
    // Build UI
    // =====================================================================

    override fun createComponent(): JComponent {
        // --- Environment ---
        val pyField = browseFile("Выберите Python интерпретатор")
        pythonField = pyField

        val envField = browseFile("Выберите .env файл")
        envFileField = envField

        val fDirField = browseDir("Выберите директорию для .feature файлов")
        featureDirField = fDirField

        // --- Main LLM ---
        val llmProv = providerCombo(); llmProviderCombo = llmProv
        val llmMod = JBTextField(); llmModelField = llmMod
        val llmTemp = tempSpinner(); llmTempSpinner = llmTemp

        // --- Validation ---
        val valIter = intSpinner(1, 10, 3); valMaxIterSpinner = valIter

        val valSame = JBCheckBox("Та же модель, что и основная LLM", true)
        valSameLlmCheckbox = valSame

        val valProv = providerCombo(); valProviderCombo = valProv
        val valMod = JBTextField(); valModelField = valMod
        val valTemp = tempSpinner(); valTempSpinner = valTemp

        valSame.addChangeListener { updateValidationFieldsEnabled() }

        // --- Embeddings ---
        val embProv = providerCombo(); embProviderCombo = embProv
        val embMod = JBTextField(); embModelField = embMod

        // --- RAG: Steps ---
        val stCol = JBTextField(); stepsCollectionField = stCol
        val stK = intSpinner(1, 50, 8); stepsTopKSpinner = stK

        // --- RAG: Docs ---
        val dcCol = JBTextField(); docsCollectionField = dcCol
        val dcPath = JBTextField(); docsPathField = dcPath
        val dcK = intSpinner(1, 50, 5); docsTopKSpinner = dcK
        val dcCS = intSpinner(100, 10_000, 1000); docsChunkSizeSpinner = dcCS
        val dcCO = intSpinner(0, 5000, 200); docsChunkOverlapSpinner = dcCO

        // --- RAG: Few Shots ---
        val fsCol = JBTextField(); fewShotsCollectionField = fsCol
        val fsK = intSpinner(1, 50, 3); fewShotsTopKSpinner = fsK
        val fsIdx = JBTextField(); fewShotsIndexField = fsIdx
        val fsDir = JBTextField(); fewShotsDirField = fsDir
        val fsBs = intSpinner(1, 1000, 100); fewShotsBatchSizeSpinner = fsBs

        // --- Docstring ---
        val dsLangs = JBTextField(); docstringLangsField = dsLangs

        // --- Layout ---
        val form = FormBuilder.createFormBuilder()

        // ========================= Окружение =========================
        form.addComponent(TitledSeparator("Окружение"))
        form.addLabeledComponent("Python:", pyField)
        form.addTooltip("Оставьте пустым — плагин сам найдёт Python и создаст venv")
        form.addLabeledComponent(".env файл:", envField)
        form.addTooltip("Файл с API-ключами (GIGACHAT_*, OPENAI_API_KEY и т.д.)")
        form.addLabeledComponent("Feature директория:", fDirField)

        // ======================= Языковая модель =====================
        form.addComponent(TitledSeparator("Языковая модель (LLM)"))
        form.addLabeledComponent("Провайдер:", llmProv)
        form.addLabeledComponent("Модель:", llmMod)
        form.addTooltip("Примеры: gpt-4.1-mini, GigaChat-2-Max")
        form.addLabeledComponent("Температура:", llmTemp)

        // ========================== Валидация =========================
        form.addComponent(TitledSeparator("Валидация feature"))
        form.addLabeledComponent("Макс. итераций:", valIter)
        form.addComponent(valSame)
        form.addLabeledComponent("Провайдер:", valProv)
        form.addLabeledComponent("Модель:", valMod)
        form.addLabeledComponent("Температура:", valTemp)

        // ========================= Эмбеддинги ========================
        form.addComponent(TitledSeparator("Эмбеддинги (RAG)"))
        form.addLabeledComponent("Провайдер:", embProv)
        form.addLabeledComponent("Модель:", embMod)
        form.addTooltip("Примеры: text-embedding-3-large, Embeddings")

        // ======================= RAG — Шаги ==========================
        form.addComponent(TitledSeparator("RAG — Шаги"))
        form.addLabeledComponent("Коллекция:", stCol)
        form.addLabeledComponent("Top K:", stK)

        // ===================== RAG — Документация =====================
        form.addComponent(TitledSeparator("RAG — Документация"))
        form.addLabeledComponent("Коллекция:", dcCol)
        form.addLabeledComponent("Путь:", dcPath)
        form.addLabeledComponent("Top K:", dcK)
        form.addLabeledComponent("Chunk size:", dcCS)
        form.addLabeledComponent("Chunk overlap:", dcCO)

        // ====================== RAG — Few Shots ======================
        form.addComponent(TitledSeparator("RAG — Few Shots"))
        form.addLabeledComponent("Коллекция:", fsCol)
        form.addLabeledComponent("Top K:", fsK)
        form.addLabeledComponent("Индекс:", fsIdx)
        form.addLabeledComponent("Директория:", fsDir)
        form.addLabeledComponent("Batch size:", fsBs)

        // ========================= Docstring =========================
        form.addComponent(TitledSeparator("Docstring"))
        form.addLabeledComponent("Языки:", dsLangs)
        form.addTooltip("Через запятую: python,json,xml,sql")

        // Spacer
        form.addComponentFillVertically(JBLabel(), 0)

        reset()
        updateValidationFieldsEnabled()

        return JBScrollPane(form.panel).apply {
            border = JBUI.Borders.empty()
        }
    }

    // =====================================================================
    // isModified / apply / reset
    // =====================================================================

    override fun isModified(): Boolean {
        val s = SpydrSettingsState.getInstance()
        return pythonField?.text != s.pythonPath ||
                envFileField?.text != s.envFilePath ||
                featureDirField?.text != s.defaultFeatureDir ||
                // LLM
                providerValue(llmProviderCombo) != s.llmProvider ||
                llmModelField?.text != s.llmModel ||
                doubleValue(llmTempSpinner) != s.llmTemperature ||
                // Validation
                intValue(valMaxIterSpinner) != s.validationMaxIterations ||
                valSameLlmCheckbox?.isSelected != s.validationUseSameLlm ||
                providerValue(valProviderCombo) != s.validationLlmProvider ||
                valModelField?.text != s.validationLlmModel ||
                doubleValue(valTempSpinner) != s.validationLlmTemperature ||
                // Embeddings
                providerValue(embProviderCombo) != s.embeddingProvider ||
                embModelField?.text != s.embeddingModel ||
                // RAG: Steps
                stepsCollectionField?.text != s.stepsCollectionName ||
                intValue(stepsTopKSpinner) != s.stepsTopK ||
                // RAG: Docs
                docsCollectionField?.text != s.docsCollectionName ||
                docsPathField?.text != s.docsPath ||
                intValue(docsTopKSpinner) != s.docsTopK ||
                intValue(docsChunkSizeSpinner) != s.docsChunkSize ||
                intValue(docsChunkOverlapSpinner) != s.docsChunkOverlap ||
                // RAG: Few Shots
                fewShotsCollectionField?.text != s.fewShotsCollectionName ||
                intValue(fewShotsTopKSpinner) != s.fewShotsTopK ||
                fewShotsIndexField?.text != s.fewShotsIndexPath ||
                fewShotsDirField?.text != s.fewShotsDir ||
                intValue(fewShotsBatchSizeSpinner) != s.fewShotsBatchSize ||
                // Docstring
                docstringLangsField?.text != s.docstringSupportedLangs
    }

    override fun apply() {
        val s = SpydrSettingsState.getInstance()
        s.pythonPath = pythonField?.text ?: ""
        s.envFilePath = envFileField?.text ?: ""
        s.defaultFeatureDir = featureDirField?.text ?: ""
        // LLM
        s.llmProvider = providerValue(llmProviderCombo)
        s.llmModel = llmModelField?.text ?: "gpt-4.1-mini"
        s.llmTemperature = doubleValue(llmTempSpinner)
        // Validation
        s.validationMaxIterations = intValue(valMaxIterSpinner)
        s.validationUseSameLlm = valSameLlmCheckbox?.isSelected ?: true
        s.validationLlmProvider = providerValue(valProviderCombo)
        s.validationLlmModel = valModelField?.text ?: "gpt-4.1-mini"
        s.validationLlmTemperature = doubleValue(valTempSpinner)
        // Embeddings
        s.embeddingProvider = providerValue(embProviderCombo)
        s.embeddingModel = embModelField?.text ?: "text-embedding-3-large"
        // RAG: Steps
        s.stepsCollectionName = stepsCollectionField?.text ?: "bdd_steps"
        s.stepsTopK = intValue(stepsTopKSpinner)
        // RAG: Docs
        s.docsCollectionName = docsCollectionField?.text ?: "project_docs"
        s.docsPath = docsPathField?.text ?: "docs"
        s.docsTopK = intValue(docsTopKSpinner)
        s.docsChunkSize = intValue(docsChunkSizeSpinner)
        s.docsChunkOverlap = intValue(docsChunkOverlapSpinner)
        // RAG: Few Shots
        s.fewShotsCollectionName = fewShotsCollectionField?.text ?: "few_shots"
        s.fewShotsTopK = intValue(fewShotsTopKSpinner)
        s.fewShotsIndexPath = fewShotsIndexField?.text ?: "src/configs/few_shots_index.json"
        s.fewShotsDir = fewShotsDirField?.text ?: "few_shots"
        s.fewShotsBatchSize = intValue(fewShotsBatchSizeSpinner)
        // Docstring
        s.docstringSupportedLangs = docstringLangsField?.text ?: "python,json,xml,sql"
    }

    override fun reset() {
        val s = SpydrSettingsState.getInstance()
        pythonField?.text = s.pythonPath
        envFileField?.text = s.envFilePath
        featureDirField?.text = s.defaultFeatureDir
        // LLM
        llmProviderCombo?.selectedItem = s.llmProvider
        llmModelField?.text = s.llmModel
        llmTempSpinner?.value = s.llmTemperature
        // Validation
        valMaxIterSpinner?.value = s.validationMaxIterations
        valSameLlmCheckbox?.isSelected = s.validationUseSameLlm
        valProviderCombo?.selectedItem = s.validationLlmProvider
        valModelField?.text = s.validationLlmModel
        valTempSpinner?.value = s.validationLlmTemperature
        // Embeddings
        embProviderCombo?.selectedItem = s.embeddingProvider
        embModelField?.text = s.embeddingModel
        // RAG: Steps
        stepsCollectionField?.text = s.stepsCollectionName
        stepsTopKSpinner?.value = s.stepsTopK
        // RAG: Docs
        docsCollectionField?.text = s.docsCollectionName
        docsPathField?.text = s.docsPath
        docsTopKSpinner?.value = s.docsTopK
        docsChunkSizeSpinner?.value = s.docsChunkSize
        docsChunkOverlapSpinner?.value = s.docsChunkOverlap
        // RAG: Few Shots
        fewShotsCollectionField?.text = s.fewShotsCollectionName
        fewShotsTopKSpinner?.value = s.fewShotsTopK
        fewShotsIndexField?.text = s.fewShotsIndexPath
        fewShotsDirField?.text = s.fewShotsDir
        fewShotsBatchSizeSpinner?.value = s.fewShotsBatchSize
        // Docstring
        docstringLangsField?.text = s.docstringSupportedLangs

        updateValidationFieldsEnabled()
    }

    override fun disposeUIResources() {
        pythonField = null; envFileField = null; featureDirField = null
        llmProviderCombo = null; llmModelField = null; llmTempSpinner = null
        valMaxIterSpinner = null; valSameLlmCheckbox = null
        valProviderCombo = null; valModelField = null; valTempSpinner = null
        embProviderCombo = null; embModelField = null
        stepsCollectionField = null; stepsTopKSpinner = null
        docsCollectionField = null; docsPathField = null; docsTopKSpinner = null
        docsChunkSizeSpinner = null; docsChunkOverlapSpinner = null
        fewShotsCollectionField = null; fewShotsTopKSpinner = null
        fewShotsIndexField = null; fewShotsDirField = null; fewShotsBatchSizeSpinner = null
        docstringLangsField = null
    }

    // =====================================================================
    // Helpers
    // =====================================================================

    private fun updateValidationFieldsEnabled() {
        val separate = valSameLlmCheckbox?.isSelected == false
        valProviderCombo?.isEnabled = separate
        valModelField?.isEnabled = separate
        valTempSpinner?.isEnabled = separate
    }

    private fun providerCombo() = ComboBox(DefaultComboBoxModel(PROVIDERS))
    private fun tempSpinner() = JSpinner(SpinnerNumberModel(0.0, 0.0, 2.0, 0.1))
    private fun intSpinner(min: Int, max: Int, value: Int) =
        JSpinner(SpinnerNumberModel(value, min, max, 1))

    private fun browseFile(title: String) = TextFieldWithBrowseButton(JBTextField()).apply {
        addBrowseFolderListener(title, null, null,
            FileChooserDescriptorFactory.createSingleFileDescriptor())
    }

    private fun browseDir(title: String) = TextFieldWithBrowseButton(JBTextField()).apply {
        addBrowseFolderListener(title, null, null,
            FileChooserDescriptorFactory.createSingleFolderDescriptor())
    }

    private fun providerValue(combo: ComboBox<String>?): String =
        combo?.selectedItem as? String ?: "openai"

    private fun intValue(spinner: JSpinner?): Int =
        (spinner?.value as? Number)?.toInt() ?: 0

    private fun doubleValue(spinner: JSpinner?): Double =
        (spinner?.value as? Number)?.toDouble() ?: 0.0

    companion object {
        private val PROVIDERS = arrayOf("openai", "gigachat")
    }
}
