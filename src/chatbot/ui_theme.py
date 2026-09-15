"""Custom properties CSS del contrato de estilo de Sue (`knowledge/estilos/README.md`).

Declara las 56 custom properties del contrato como un único bloque ``:root``, con los
valores del estilo `minimalista` (ver `## Anexo: config.toml y bloque CSS propuestos` de
`docs/diseno/consolidado.md` y ADR-022). `app.py` inyecta ``THEME_CSS`` una sola vez, vía
`st.markdown(..., unsafe_allow_html=True)`, inmediatamente después de `st.set_page_config`.

Este módulo solo declara las variables. Las reglas CSS que las consumen sobre selectores
concretos (foco del input, separación de turnos del chat, contraste de `stAlert`, etc.) se
agregan en los cambios siguientes (`CAMBIO-04`..`CAMBIO-09` de `docs/diseno/consolidado.md`).
"""

THEME_CSS = """
<style>
/* Chatbot de datos — tokens (base: minimalista) — contrato knowledge/estilos/README.md de Sue */
:root {
  --color-primary: #111111;
  --color-primary-hover: #000000;
  --color-primary-contrast: #ffffff;
  --color-accent: #111111;
  --color-bg-page: #ffffff;
  --color-bg-surface: #ffffff;
  --color-bg-muted: #f7f7f7;
  --color-text: #111111;
  --color-text-secondary: #555555;
  --color-text-muted: #8a8a8a;
  --color-link: #111111;
  --color-border: #e6e6e6;
  --color-border-strong: #cccccc;
  --color-focus: #111111;
  --color-success: #1a7f37;
  --color-success-bg: #eef8f0;
  --color-warning: #9a6700;
  --color-warning-bg: #fff8e1;
  --color-error: #b42318;
  --color-error-bg: #fdecec;
  --font-body: "Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-heading: "Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, monospace;
  --font-size-sm: 0.875rem;
  --font-size-base: 16px;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.375rem;
  --font-size-2xl: 1.75rem;
  --font-size-3xl: 2.25rem;
  --line-height-base: 1.6;
  --line-height-heading: 1.2;
  --font-weight-normal: 400;
  --font-weight-semibold: 500;
  --font-weight-bold: 600;
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 1rem;
  --space-4: 1.5rem;
  --space-5: 2rem;
  --space-6: 3rem;
  --space-7: 4rem;
  --space-8: 6rem;
  --max-width-content: 680px;
  --max-width-wide: 1120px;
  --sidebar-width: 240px;
  --navbar-height: 56px;
  --padding-x-page: 1.5rem;
  --padding-y-page: 3rem;
  --radius-sm: 2px;
  --radius-md: 4px;
  --radius-lg: 6px;
  --radius-pill: 999px;
  --border-width: 1px;
  --shadow-sm: none;
  --shadow-md: 0 1px 2px rgba(0, 0, 0, 0.04);
  --transition-fast: 150ms ease;
}

/* Anillo de foco visible del input del chat (TECH-111). El data-testid
   "stChatInputTextArea" está verificado para Streamlit 1.63.0 (ver
   docs/diseno/00-estado-actual.md) y puede cambiar entre versiones. */
[data-testid="stChatInputTextArea"]:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
  transition: outline-color var(--transition-fast);
}

/* Separación vertical entre turnos del historial de chat (TECH-112), para diferenciarlos
   sin depender solo del avatar default de `st.chat_message`. El data-testid
   "stChatMessage" está verificado para Streamlit 1.63.0 y puede cambiar entre versiones. */
[data-testid="stChatMessage"] {
  margin-bottom: var(--space-3);
}

/* Contraste AA de st.warning / st.error (TECH-113). El contenedor de alerta expone
   data-testid="stAlertContainer" (con role="alert") y, como hijo, un data-testid
   "stAlertContent${Kind}" (ej. "stAlertContentWarning", "stAlertContentError") construido
   en runtime a partir del tipo de alerta — no aparece literal en el bundle JS minificado.
   Verificado para Streamlit 1.63.0 (ver docs/diseno/00-estado-actual.md); puede cambiar
   entre versiones.
   Ratios WCAG calculados (luminancia relativa, canales linealizados):
   --color-warning #9a6700 sobre --color-warning-bg #fff8e1 → 4.58:1 (cumple AA ≥4.5:1).
   --color-error #b42318 sobre --color-error-bg #fdecec → 5.76:1 (cumple AA ≥4.5:1). */
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) {
  background-color: var(--color-warning-bg);
}
[data-testid="stAlertContentWarning"] {
  color: var(--color-warning);
}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) {
  background-color: var(--color-error-bg);
}
[data-testid="stAlertContentError"] {
  color: var(--color-error);
}

/* Tipografía monoespaciada acotada al caption del dataset (TECH-116), p.ej. "archivo —
   N filas, M columnas". No se extiende al cuerpo del chat ni a la explicación (ADR-021/022).
   El data-testid "stCaptionContainer" está verificado para Streamlit 1.63.0 y puede cambiar
   entre versiones. */
[data-testid="stCaptionContainer"] {
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
}
</style>
"""
