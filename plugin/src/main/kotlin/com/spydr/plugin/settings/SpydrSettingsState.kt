package com.spydr.plugin.settings

import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.components.PersistentStateComponent
import com.intellij.openapi.components.State
import com.intellij.openapi.components.Storage
import com.intellij.openapi.diagnostic.Logger
import java.io.File

/**
 * Persistent application-level settings for the SpyDR plugin.
 *
 * Contains **all** configuration values that were previously split
 * between `src/agents/config.yml` and `src/configs/config.yml`.
 * Before starting the Python backend, [com.spydr.plugin.backend.ConfigWriter]
 * generates both YAML files from this state.
 */
@State(
    name = "com.spydr.plugin.settings.SpydrSettingsState",
    storages = [Storage("SpydrPlugin.xml")]
)
class SpydrSettingsState : PersistentStateComponent<SpydrSettingsState.State> {

    data class State(
        // ---- Environment ------------------------------------------------
        /** Python interpreter path. Empty → auto mode (bundled venv). */
        var pythonPath: String = "",
        /** Default directory for generated .feature files. */
        var defaultFeatureDir: String = "",
        /** Path to .env file with API keys. */
        var envFilePath: String = "",

        // ---- Main LLM ---------------------------------------------------
        var llmProvider: String = "openai",
        var llmModel: String = "gpt-4.1-mini",
        var llmTemperature: Double = 0.0,

        // ---- Validation --------------------------------------------------
        var validationMaxIterations: Int = 3,
        /** When true, validation uses the same LLM as the main agent. */
        var validationUseSameLlm: Boolean = true,
        var validationLlmProvider: String = "openai",
        var validationLlmModel: String = "gpt-4.1-mini",
        var validationLlmTemperature: Double = 0.0,

        // ---- Embeddings --------------------------------------------------
        var embeddingProvider: String = "openai",
        var embeddingModel: String = "text-embedding-3-large",

        // ---- RAG: Steps --------------------------------------------------
        var stepsCollectionName: String = "bdd_steps",
        var stepsTopK: Int = 8,

        // ---- RAG: Docs ---------------------------------------------------
        var docsCollectionName: String = "project_docs",
        var docsPath: String = "docs",
        var docsTopK: Int = 5,
        var docsChunkSize: Int = 1000,
        var docsChunkOverlap: Int = 200,

        // ---- RAG: Few Shots ----------------------------------------------
        var fewShotsCollectionName: String = "few_shots",
        var fewShotsTopK: Int = 3,
        var fewShotsIndexPath: String = "src/configs/few_shots_index.json",
        var fewShotsDir: String = "few_shots",
        var fewShotsBatchSize: Int = 100,

        // ---- Docstring ---------------------------------------------------
        var docstringSupportedLangs: String = "python,json,xml,sql",
    )

    private var myState = State()

    override fun getState(): State = myState
    override fun loadState(state: State) { myState = state }

    // ---- Convenience accessors (delegating to myState) -------------------

    var pythonPath: String
        get() = myState.pythonPath; set(v) { myState.pythonPath = v }
    var defaultFeatureDir: String
        get() = myState.defaultFeatureDir; set(v) { myState.defaultFeatureDir = v }
    var envFilePath: String
        get() = myState.envFilePath; set(v) { myState.envFilePath = v }

    var llmProvider: String
        get() = myState.llmProvider; set(v) { myState.llmProvider = v }
    var llmModel: String
        get() = myState.llmModel; set(v) { myState.llmModel = v }
    var llmTemperature: Double
        get() = myState.llmTemperature; set(v) { myState.llmTemperature = v }

    var validationMaxIterations: Int
        get() = myState.validationMaxIterations; set(v) { myState.validationMaxIterations = v }
    var validationUseSameLlm: Boolean
        get() = myState.validationUseSameLlm; set(v) { myState.validationUseSameLlm = v }
    var validationLlmProvider: String
        get() = myState.validationLlmProvider; set(v) { myState.validationLlmProvider = v }
    var validationLlmModel: String
        get() = myState.validationLlmModel; set(v) { myState.validationLlmModel = v }
    var validationLlmTemperature: Double
        get() = myState.validationLlmTemperature; set(v) { myState.validationLlmTemperature = v }

    var embeddingProvider: String
        get() = myState.embeddingProvider; set(v) { myState.embeddingProvider = v }
    var embeddingModel: String
        get() = myState.embeddingModel; set(v) { myState.embeddingModel = v }

    var stepsCollectionName: String
        get() = myState.stepsCollectionName; set(v) { myState.stepsCollectionName = v }
    var stepsTopK: Int
        get() = myState.stepsTopK; set(v) { myState.stepsTopK = v }

    var docsCollectionName: String
        get() = myState.docsCollectionName; set(v) { myState.docsCollectionName = v }
    var docsPath: String
        get() = myState.docsPath; set(v) { myState.docsPath = v }
    var docsTopK: Int
        get() = myState.docsTopK; set(v) { myState.docsTopK = v }
    var docsChunkSize: Int
        get() = myState.docsChunkSize; set(v) { myState.docsChunkSize = v }
    var docsChunkOverlap: Int
        get() = myState.docsChunkOverlap; set(v) { myState.docsChunkOverlap = v }

    var fewShotsCollectionName: String
        get() = myState.fewShotsCollectionName; set(v) { myState.fewShotsCollectionName = v }
    var fewShotsTopK: Int
        get() = myState.fewShotsTopK; set(v) { myState.fewShotsTopK = v }
    var fewShotsIndexPath: String
        get() = myState.fewShotsIndexPath; set(v) { myState.fewShotsIndexPath = v }
    var fewShotsDir: String
        get() = myState.fewShotsDir; set(v) { myState.fewShotsDir = v }
    var fewShotsBatchSize: Int
        get() = myState.fewShotsBatchSize; set(v) { myState.fewShotsBatchSize = v }

    var docstringSupportedLangs: String
        get() = myState.docstringSupportedLangs; set(v) { myState.docstringSupportedLangs = v }

    // ---- Computed properties ---------------------------------------------

    val isAutoMode: Boolean
        get() = myState.pythonPath.isBlank()

    /**
     * Build the full set of environment variables for the Python subprocess.
     *
     * 1. Finds the `.env` file — either explicitly configured in
     *    [envFilePath], or auto-detected in the [projectRoot].
     * 2. Parses `KEY=VALUE` lines from that file and adds them to the map.
     * 3. Sets `SPYDR_DOTENV_PATH` so the Python code can also pick it up.
     *
     * This ensures the subprocess always has the API keys even when it
     * starts in a different working directory (e.g. `~/.spydr/backend/`).
     */
    fun buildEnvOverrides(projectRoot: String? = null): Map<String, String> {
        val env = mutableMapOf<String, String>()

        // Resolve .env file
        val dotEnvFile = resolveDotEnv(projectRoot)
        if (dotEnvFile != null) {
            env["SPYDR_DOTENV_PATH"] = dotEnvFile.absolutePath
            // Parse and inject all KEY=VALUE pairs from .env
            parseDotEnv(dotEnvFile).forEach { (k, v) -> env[k] = v }
        }

        return env
    }

    /**
     * Find the `.env` file: first check [envFilePath], then
     * `<projectRoot>/.env`.
     */
    private fun resolveDotEnv(projectRoot: String?): File? {
        if (envFilePath.isNotBlank()) {
            val f = File(envFilePath)
            if (f.isFile) return f
        }
        if (projectRoot != null) {
            val f = File(projectRoot, ".env")
            if (f.isFile) return f
        }
        return null
    }

    /**
     * Minimal `.env` parser — handles `KEY=VALUE`, strips optional
     * quotes, ignores comments and blank lines.
     */
    private fun parseDotEnv(file: File): Map<String, String> {
        val result = mutableMapOf<String, String>()
        try {
            file.readLines().forEach { raw ->
                val line = raw.trim()
                if (line.isEmpty() || line.startsWith("#")) return@forEach
                val idx = line.indexOf('=')
                if (idx <= 0) return@forEach
                val key = line.substring(0, idx).trim()
                var value = line.substring(idx + 1).trim()
                // Strip surrounding quotes (single or double)
                if (value.length >= 2 &&
                    ((value.startsWith("\"") && value.endsWith("\"")) ||
                     (value.startsWith("'") && value.endsWith("'")))) {
                    value = value.substring(1, value.length - 1)
                }
                result[key] = value
            }
        } catch (e: Exception) {
            LOG.warn("Failed to parse .env file: ${file.absolutePath}", e)
        }
        return result
    }

    companion object {
        private val LOG = Logger.getInstance(SpydrSettingsState::class.java)

        fun getInstance(): SpydrSettingsState =
            ApplicationManager.getApplication().getService(SpydrSettingsState::class.java)
    }
}
