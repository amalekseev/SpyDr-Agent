package com.spydr.plugin.backend

import com.google.gson.Gson
import com.google.gson.JsonObject

/**
 * JSON-lines protocol encoder/decoder for communication with the Python backend.
 */
object MessageProtocol {

    private val gson = Gson()

    // -----------------------------------------------------------------------
    // Outgoing (plugin -> python stdin)
    // -----------------------------------------------------------------------

    fun buildChatMessage(
        message: String,
        projectId: String,
        featureFilePath: String,
        validationEnabled: Boolean,
        maxValidationIterations: Int,
    ): String {
        val config = JsonObject().apply {
            addProperty("project_id", projectId)
            addProperty("feature_file_path", featureFilePath)
            addProperty("validation_enabled", validationEnabled)
            addProperty("max_validation_iterations", maxValidationIterations)
        }
        val root = JsonObject().apply {
            addProperty("type", "chat")
            addProperty("message", message)
            add("config", config)
        }
        return gson.toJson(root)
    }

    fun buildResetMessage(): String {
        val root = JsonObject().apply {
            addProperty("type", "reset")
        }
        return gson.toJson(root)
    }

    fun buildListProjectsMessage(): String {
        val root = JsonObject().apply {
            addProperty("type", "list_projects")
        }
        return gson.toJson(root)
    }

    // -----------------------------------------------------------------------
    // Incoming (python stdout -> plugin)
    // -----------------------------------------------------------------------

    data class IncomingMessage(
        val type: String,
        val content: String = "",
        val path: String = "",
        val projects: List<String> = emptyList(),
    )

    fun parse(jsonLine: String): IncomingMessage? {
        return try {
            val obj = gson.fromJson(jsonLine, JsonObject::class.java) ?: return null
            val type = obj.get("type")?.asString ?: return null
            val content = obj.get("content")?.asString ?: ""
            val path = obj.get("path")?.asString ?: ""
            val projects = if (obj.has("projects")) {
                obj.getAsJsonArray("projects").map { it.asString }
            } else {
                emptyList()
            }
            IncomingMessage(type = type, content = content, path = path, projects = projects)
        } catch (e: Exception) {
            null
        }
    }
}
