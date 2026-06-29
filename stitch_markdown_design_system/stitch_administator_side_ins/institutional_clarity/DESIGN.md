---
name: Institutional Clarity
colors:
  surface: '#f7f9fc'
  surface-dim: '#d8dadd'
  surface-bright: '#f7f9fc'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f7'
  surface-container: '#eceef1'
  surface-container-high: '#e6e8eb'
  surface-container-highest: '#e0e3e6'
  on-surface: '#191c1e'
  on-surface-variant: '#424750'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f4'
  outline: '#727781'
  outline-variant: '#c2c7d1'
  surface-tint: '#27609c'
  primary: '#003866'
  on-primary: '#ffffff'
  primary-container: '#0b4f8a'
  on-primary-container: '#94c2ff'
  inverse-primary: '#a2c9ff'
  secondary: '#006874'
  on-secondary: '#ffffff'
  secondary-container: '#84ecfd'
  on-secondary-container: '#006b77'
  tertiary: '#592a00'
  on-tertiary: '#ffffff'
  tertiary-container: '#7b3c00'
  on-tertiary-container: '#ffab6f'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d3e4ff'
  primary-fixed-dim: '#a2c9ff'
  on-primary-fixed: '#001c38'
  on-primary-fixed-variant: '#004881'
  secondary-fixed: '#99f0ff'
  secondary-fixed-dim: '#6cd5e6'
  on-secondary-fixed: '#001f24'
  on-secondary-fixed-variant: '#004f58'
  tertiary-fixed: '#ffdcc6'
  tertiary-fixed-dim: '#ffb785'
  on-tertiary-fixed: '#301400'
  on-tertiary-fixed-variant: '#713700'
  background: '#f7f9fc'
  on-background: '#191c1e'
  surface-variant: '#e0e3e6'
  text-main: '#1F2933'
  text-muted: '#667085'
  success: '#1E8E5A'
  warning: '#D98A00'
  danger: '#C0392B'
  border: '#E2E8F0'
  surface-card: '#FFFFFF'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: '700'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  button:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: '1'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  sidebar-width: 280px
  topbar-height: 64px
  container-gap: 24px
  form-element-height: 48px
  gutter-md: 1.5rem
  margin-page: 2rem
---

## Brand & Style

This design system is engineered for the **INS Survey Collection Platform**, prioritizing institutional trust, administrative efficiency, and absolute clarity. The target audience includes government employees and corporate contacts who require a tool that minimizes cognitive load and maximizes data accuracy.

The visual style is **Corporate / Modern**, heavily influenced by established Material Design principles and Bootstrap's functional utility. It avoids all decorative elements, gradients, and unnecessary imagery in favor of a "form follows function" philosophy. The emotional response should be one of professional calm, stability, and reliability. High-contrast interfaces and generous whitespace ensure the system remains accessible to older and non-technical users, making navigation intuitive and "obvious."

## Colors

The palette is rooted in an **Institutional Blue** to convey authority and officiality. A secondary teal accent provides subtle distinction for interactive elements without introducing visual noise.

- **Primary Blue (#0B4F8A):** Used for primary buttons, active navigation states, and key headers.
- **Background (#F4F6F9):** A soft, cool gray used for the application stage to reduce eye strain.
- **Semantic Colors:** Success, Warning, and Danger colors are used strictly for status indicators and destructive actions. Status chips must pair these colors with clear text labels to ensure accessibility for color-blind users.
- **Neutral Stack:** A high-contrast text hierarchy (Main: #1F2933 vs Muted: #667085) ensures legibility against the white surface cards.

## Typography

The system utilizes **Inter** for its exceptional legibility in data-heavy environments. The scale is intentionally generous to accommodate users with varying degrees of visual acuity.

- **Scale:** Body text never drops below 16px. Titles range from 24px to 28px to establish clear page hierarchy.
- **Hierarchy:** Use `headline-lg` for primary page titles and `headline-md` for card titles or section headers.
- **Labels:** Form labels use a semi-bold weight (`label-lg`) positioned strictly above the input fields to maintain a consistent vertical scanning path.
- **Helper Text:** Use `label-sm` in the muted text color for instructions or field hints located immediately below input fields.

## Layout & Spacing

The layout follows a **Fixed Sidebar** model for the desktop experience, providing constant access to the primary navigation items. 

- **App Shell:** A white fixed left sidebar (280px) houses the logo and vertical navigation. A slim top bar contains context-specific information like page titles and notifications.
- **Main Stage:** Content is contained within white cards on the light-gray background, using a 24px (1.5rem) grid for gutters and margins.
- **Mobile Adaptivity (≤480px):** 
    - The sidebar transitions to a hamburger drawer.
    - All 2-column or 3-column card layouts collapse into a single vertical column.
    - Interactive elements (buttons/inputs) stretch to 100% width.
    - Data tables reflow into a "Card List" format where each row becomes a card with labels stacked above values.

## Elevation & Depth

To maintain a "clean and calm" aesthetic, the system uses **Low-contrast outlines** and subtle tonal layering rather than heavy shadows.

- **Cards:** Use a 1px solid border (#E2E8F0) to define boundaries on the light-gray background. Do not use drop shadows for standard containers.
- **Modals & Dialogs:** Use a soft, centered ambient shadow to distinguish overlays from the main content. A semi-transparent dark overlay must dim the background to focus attention.
- **Sidebar:** Elevated by a thin vertical border on the right (#E2E8F0) to separate navigation from the workspace without creating a visual "heavy" edge.

## Shapes

The shape language is **Soft**, utilizing small border radii to take the edge off the interface while maintaining a structured, professional appearance.

- **Components:** Standard buttons, input fields, and cards use a 0.25rem (4px) corner radius.
- **Status Chips:** Use a fully rounded (pill) shape to distinguish them from interactive buttons.
- **Navigation Highlight:** Use a soft-rounded rectangle for the active state in the sidebar, ensuring the highlight does not touch the sidebar edges.

## Components

### Buttons
- **Height:** Exactly 48px.
- **Primary:** Filled Blue (#0B4F8A) with White text. Limit to **one** per screen.
- **Secondary:** Outlined (#0B4F8A border) or Ghost (Text only).
- **Destructive:** Outlined Danger (#C0392B) with a confirmation dialog required before execution.

### Input Fields
- **Height:** 48px.
- **Structure:** Label (Semi-bold, 14px) always visible above the field. 1px border (#E2E8F0).
- **Focus State:** 2px solid border using the Secondary teal (#1B98A8).

### Status Chips
- **Style:** Small pill-shaped containers.
- **Colors:** Use semantic palette. High-contrast text is mandatory (e.g., dark green text on a light green background, or white text on the semantic base).
- **Constraint:** Never use color alone to convey status; always include a text label.

### Lists & Tables
- **Desktop:** Standard rows with 16px vertical padding and subtle bottom borders.
- **Mobile:** Transformed into stacked cards. Label text should be muted, value text should be primary text.

### Breadcrumbs
- **Requirement:** Mandatory on all inner pages, located directly below the top bar title to provide immediate spatial orientation.