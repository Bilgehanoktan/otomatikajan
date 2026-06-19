/**
 * Sovereign AGI - Component Loader V1.0
 * Handles dynamic injection of modular dashboard components.
 */
const ComponentLoader = {
    async load(id, url) {
        const container = document.getElementById(id);
        if (!container) return;

        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const html = await response.text();
            container.innerHTML = html;
            console.log(`[ComponentLoader] Loaded ${url} into #${id}`);
        } catch (error) {
            console.error(`[ComponentLoader] Failed to load ${url}:`, error);
            container.innerHTML = `<div class="error-msg">Failed to load component: ${url}</div>`;
        }
    },

    async loadAll(mappings) {
        const promises = Object.entries(mappings).map(([id, url]) => this.load(id, url));
        return Promise.all(promises);
    }
};

window.ComponentLoader = ComponentLoader;
