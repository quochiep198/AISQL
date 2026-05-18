---
name: Technical Precision
colors:
  surface: '#0e1417'
  surface-dim: '#0e1417'
  surface-bright: '#333a3d'
  surface-container-lowest: '#090f12'
  surface-container-low: '#161d1f'
  surface-container: '#1a2123'
  surface-container-high: '#242b2e'
  surface-container-highest: '#2f3639'
  on-surface: '#dde3e7'
  on-surface-variant: '#bbc9cf'
  inverse-surface: '#dde3e7'
  inverse-on-surface: '#2b3134'
  outline: '#859399'
  outline-variant: '#3c494e'
  surface-tint: '#4cd6ff'
  primary: '#a4e6ff'
  on-primary: '#003543'
  primary-container: '#00d1ff'
  on-primary-container: '#00566a'
  inverse-primary: '#00677f'
  secondary: '#b7c8e1'
  on-secondary: '#213145'
  secondary-container: '#3a4a5f'
  on-secondary-container: '#a9bad3'
  tertiary: '#ffd59c'
  on-tertiary: '#442b00'
  tertiary-container: '#feb127'
  on-tertiary-container: '#6b4700'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#b7eaff'
  primary-fixed-dim: '#4cd6ff'
  on-primary-fixed: '#001f28'
  on-primary-fixed-variant: '#004e60'
  secondary-fixed: '#d3e4fe'
  secondary-fixed-dim: '#b7c8e1'
  on-secondary-fixed: '#0b1c30'
  on-secondary-fixed-variant: '#38485d'
  tertiary-fixed: '#ffddb1'
  tertiary-fixed-dim: '#ffba49'
  on-tertiary-fixed: '#291800'
  on-tertiary-fixed-variant: '#624000'
  background: '#0e1417'
  on-background: '#dde3e7'
  surface-variant: '#2f3639'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  code-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  sidebar-width: 280px
  gutter: 1px
---

## Brand & Style
The design system is engineered for high-performance database management and optimization. It evokes an emotional response of absolute control, technical authority, and clarity. The brand personality is professional, unsentimental, and highly efficient, catering to developers and DBA professionals who require an environment free from visual clutter.

The aesthetic follows a **Minimalist Corporate** approach with a focus on "Functional Density." It prioritizes information hierarchy through crisp lines, strategic use of color for semantic meaning, and a structured layout reminiscent of high-end Integrated Development Environments (IDEs). The UI remains unobtrusive to ensure the user's primary focus remains on the logic and performance of their code.

## Colors
The palette is optimized for long-duration technical work, utilizing a deep navy and slate foundation to reduce eye strain.

- **Primary**: A vibrant Cyan (#00D1FF) is reserved for the most critical actions and primary navigation states.
- **Semantic Palette**: Functional colors are highly saturated to ensure they stand out against the dark backgrounds. Success (Green) indicates optimized paths, Warning (Amber) highlights performance bottlenecks or non-indexed scans, and Error (Red) identifies syntax failures or critical risks.
- **Neutral/Surface**: Multiple tiers of slate are used to create structural separation without relying on heavy shadows. Surfaces are layered to distinguish between navigation, sidebars, and the primary editing canvas.

## Typography
The system employs a dual-typeface strategy to separate the interface from the data. 

**Inter** is the primary UI face, selected for its exceptional legibility in dense settings. Use tighter letter-spacing for headlines to maintain a modern, "compact" feel.

**JetBrains Mono** is mandatory for all SQL/NoSQL code blocks, query results, and execution plans. The increased line height in the `code-md` role ensures that complex nested queries remain readable. All labels for metrics (e.g., "Execution Time") should use the uppercase `label-md` style to provide distinct visual separation from content values.

## Layout & Spacing
This design system utilizes a **Structured Tool Layout** centered around a core workspace. It follows a strict 4px grid system.

- **Desktop**: A three-pane layout is standard. The Left Sidebar (280px) handles navigation and schema browsing; the Center Canvas is fluid for code entry; the Right Sidebar (Variable) is used for "Analysis & Optimization" insights.
- **Grids**: Use 1px gutters for internal card divisions to create a "panelled" look typical of modern IDEs. 
- **Reflow**: On smaller screens, sidebars collapse into icons or move into drawers, prioritizing the code editor. The main content area should never have less than 16px of horizontal padding.

## Elevation & Depth
Depth is achieved primarily through **Tonal Layering** and **Low-Contrast Outlines** rather than traditional drop shadows.

- **Background**: The lowest layer (#0F172A). Used for the application shell.
- **Surface-Low**: Slightly lighter (#1E293B). Used for sidebars and secondary containers.
- **Surface-High**: The lightest core surface (#334155). Reserved for active code editors and modal overlays.
- **Borders**: All containers must have a 1px solid border (#30363D). This provides the "technical" definition required for high-density tools. Shadows are used only for floating menus or modals, appearing as a subtle 8px blur with 40% opacity in a true-black tint.

## Shapes
The shape language is **Soft (0.25rem)**. This subtle rounding maintains the professional "boxiness" of a developer tool while preventing the UI from feeling dated or harsh.

- **Buttons & Inputs**: Use 4px (0.25rem) corner radius.
- **Cards & Panes**: Use 8px (0.5rem) for outer containers to create a distinct hierarchy between the container and the elements inside it.
- **Status Badges**: Use a fully rounded pill shape to distinguish them clearly from interactive buttons.

## Components
- **Code Editor**: The centerpiece. It must include line numbering, a subtle vertical "ruler" at 80/120 characters, and syntax highlighting following the primary/semantic color rules.
- **Action Buttons**: Primary buttons use the vibrant Cyan background with dark text. Secondary buttons use a ghost style with a subtle slate border.
- **Tabs**: Use a flat, underline-style tab system for switching between SQL and NoSQL. The active state is indicated by a 2px Cyan bottom border.
- **Risk Badges**: Small, semi-transparent chips with a solid dot icon. The color of the dot and the text must correspond to the Semantic Palette (Success/Warning/Error).
- **Analysis Sidebars**: Content should be organized into collapsible "Accordions" with 1px slate borders.
- **Input Fields**: Dark backgrounds with 1px slate borders. On focus, the border transitions to Cyan with a 2px outer glow.