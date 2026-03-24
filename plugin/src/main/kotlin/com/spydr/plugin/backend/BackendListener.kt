package com.spydr.plugin.backend

/**
 * Callback interface for events coming from the Python backend process.
 */
interface BackendListener {
    /** Agent streamed a text chunk (assistant message). */
    fun onText(content: String)

    /** Agent sent a status update (e.g. "Ищу шаги…"). */
    fun onStatus(content: String)

    /** Feature file has been written to disk. */
    fun onFeatureWritten(path: String)

    /** Backend signaled that the current request is done. */
    fun onDone()

    /** An error occurred in the backend. */
    fun onError(content: String)

    /** Backend process started and is ready. */
    fun onReady(projects: List<String>)

    /** Session has been reset. */
    fun onSessionReset()
}
