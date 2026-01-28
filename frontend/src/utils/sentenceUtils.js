/**
 * Utility functions for sentence processing
 * Used by the frontend to split and validate Dutch text before sending to backend
 */

/**
 * Split text into sentences by common sentence-ending punctuation
 * @param {string} text - The text to split
 * @returns {string[]} Array of sentence fragments
 */
export function splitSentences(text) {
    // Split by common sentence-ending punctuation (.!?)
    const sentences = text.split(/[.!?]+/)
        .map(s => s.trim())
        .filter(Boolean)
    return sentences
}

/**
 * Check if a sentence is valid (contains at least one word)
 * A valid sentence must have at least one letter sequence (including accented characters)
 * @param {string} sentence - The sentence to validate
 * @returns {boolean} True if valid, false otherwise
 */
export function isValidSentence(sentence) {
    // Check if sentence contains at least one word (letter sequence)
    // Pattern matches English letters (a-z, A-Z) and accented characters (À-ÿ)
    // This supports Dutch, French, German, Spanish, Portuguese, Italian, etc.
    const hasWord = /[a-zA-Z\u00C0-\u00FF]+/.test(sentence)
    return hasWord
}

/**
 * Filter sentences to keep only valid ones
 * Removes fragments like "!!!", "123", '""', etc. that don't contain actual words
 * @param {string[]} sentences - Array of sentence fragments
 * @returns {string[]} Array of valid sentences only
 */
export function filterValidSentences(sentences) {
    return sentences.filter(isValidSentence)
}

/**
 * Complete pipeline: split text into sentences and validate them
 * @param {string} text - The text to process
 * @returns {string[]} Array of valid sentences ready for LLM analysis
 */
export function prepareSentences(text) {
    const sentences = splitSentences(text)
    return filterValidSentences(sentences)
}
