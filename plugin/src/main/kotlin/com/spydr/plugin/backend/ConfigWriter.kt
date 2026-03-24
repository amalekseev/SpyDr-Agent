package com.spydr.plugin.backend

import com.intellij.openapi.diagnostic.Logger
import com.spydr.plugin.settings.SpydrSettingsState
import java.nio.file.Files
import java.nio.file.Path

/**
 * Generates `src/agents/config.yml` and `src/configs/config.yml` from
 * plugin settings and writes them to the backend working directory.
 *
 * Must be called **before** the Python process is started so that
 * the configs are read by `OmegaConf.load(...)` at import time.
 */
object ConfigWriter {

    private val LOG = Logger.getInstance(ConfigWriter::class.java)

    /**
     * Write both config files under [workingDir].
     *
     * @param workingDir root of the Python backend
     *                   (e.g. `~/.spydr/backend/` or project base path).
     */
    fun writeConfigs(workingDir: Path) {
        val s = SpydrSettingsState.getInstance()
        writeAgentConfig(workingDir.resolve("src/agents/config.yml"), s)
        writeGlobalConfig(workingDir.resolve("src/configs/config.yml"), s)
    }

    // -------------------------------------------------------------------
    // src/agents/config.yml
    // -------------------------------------------------------------------

    private fun writeAgentConfig(path: Path, s: SpydrSettingsState) {
        val valProvider = if (s.validationUseSameLlm) s.llmProvider else s.validationLlmProvider
        val valModel    = if (s.validationUseSameLlm) s.llmModel else s.validationLlmModel
        val valTemp     = if (s.validationUseSameLlm) s.llmTemperature else s.validationLlmTemperature

        val yaml = buildString {
            appendLine("llm_params:")
            appendLine("  provider: ${s.llmProvider}")
            appendLine("  model: ${s.llmModel}")
            appendLine("  temperature: ${fmtNum(s.llmTemperature)}")
            appendLine()
            appendLine("validation:")
            appendLine("  max_iterations: ${s.validationMaxIterations}")
            appendLine("  llm_params:")
            appendLine("    provider: $valProvider")
            appendLine("    model: $valModel")
            appendLine("    temperature: ${fmtNum(valTemp)}")
        }

        writeFile(path, yaml)
        LOG.info("Wrote agent config to $path")
    }

    // -------------------------------------------------------------------
    // src/configs/config.yml
    // -------------------------------------------------------------------

    private fun writeGlobalConfig(path: Path, s: SpydrSettingsState) {
        val langs = s.docstringSupportedLangs
            .split(",")
            .map { it.trim() }
            .filter { it.isNotEmpty() }

        val yaml = buildString {
            appendLine("rag:")
            appendLine("  provider: ${s.embeddingProvider}")
            appendLine("  params:")
            appendLine("    model: ${s.embeddingModel}")
            appendLine()
            appendLine("  steps:")
            appendLine("    collection_name: ${s.stepsCollectionName}")
            appendLine("    top_k: ${s.stepsTopK}")
            appendLine()
            appendLine("  docs:")
            appendLine("    collection_name: ${s.docsCollectionName}")
            appendLine("    path: ${s.docsPath}")
            appendLine("    top_k: ${s.docsTopK}")
            appendLine("    chunk_size: ${s.docsChunkSize}")
            appendLine("    chunk_overlap: ${s.docsChunkOverlap}")
            appendLine()
            appendLine("  few_shots:")
            appendLine("    collection_name: ${s.fewShotsCollectionName}")
            appendLine("    top_k: ${s.fewShotsTopK}")
            appendLine("    index_path: ${s.fewShotsIndexPath}")
            appendLine("    few_shots_dir: ${s.fewShotsDir}")
            appendLine("    batch_size: ${s.fewShotsBatchSize}")
            appendLine()
            appendLine("docstring:")
            appendLine("  supported_langs:")
            for (lang in langs) {
                appendLine("    - $lang")
            }
        }

        writeFile(path, yaml)
        LOG.info("Wrote global config to $path")
    }

    // -------------------------------------------------------------------
    // Helpers
    // -------------------------------------------------------------------

    private fun writeFile(path: Path, content: String) {
        Files.createDirectories(path.parent)
        Files.writeString(path, content)
    }

    /** Format a double: 0.0 → "0", 0.7 → "0.7" */
    private fun fmtNum(d: Double): String {
        return if (d == d.toLong().toDouble()) d.toLong().toString() else d.toString()
    }
}
