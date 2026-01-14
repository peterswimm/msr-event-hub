# Accessibility (WCAG 2.1 AA Compliance)

This document outlines the accessibility features and testing tools configured for the MSR Event Agent Chat application.

## Accessibility Tools & Configuration

### ESLint Integration (Static Analysis)
- **Package**: `eslint-plugin-jsx-a11y`
- **Configuration**: `.eslintrc.json`
- **Rules Enforced**:
  - `jsx-a11y/alt-text: error` - Images require alt text
  - `jsx-a11y/aria-props: error` - Valid ARIA properties
  - `jsx-a11y/aria-proptypes: error` - Correct ARIA property types
  - `jsx-a11y/aria-unsupported-elements: warn` - No ARIA on unsupported elements
  - `jsx-a11y/heading-has-content: error` - Headings must have content
  - `jsx-a11y/html-has-lang: error` - HTML must have lang attribute
  - `jsx-a11y/label-has-associated-control: warn` - Labels must be associated with controls
  - `jsx-a11y/no-noninteractive-element-interactions: warn` - No interactions on non-interactive elements
  - `jsx-a11y/role-has-required-aria-props: error` - Required ARIA props for roles
  - `jsx-a11y/click-events-have-key-events: warn` - Click handlers need keyboard equivalents

### Runtime Testing (Development Only)
- **Package**: `@axe-core/react`, `axe-core`
- **Configuration**: `main.tsx`
- **Activation**: Set `VITE_A11Y=true` in `.env` file
- **Behavior**: Runs axe-core accessibility audits in browser console (DEV mode only)
- **Output**: Console logs accessibility violations with severity, description, and affected elements

## Component Accessibility Features

### ProjectCarousel
- **Keyboard Navigation**: Arrow buttons fully keyboard accessible
- **ARIA Labels**: 
  - `aria-label="Previous project"` on prev button
  - `aria-label="Next project"` on next button
  - `role="region"` with `aria-label="Project carousel"` on container
  - `role="group"` with `aria-live="polite"` on carousel content for screen reader updates
- **Semantic HTML**: Uses `<h3>` for project titles
- **Focus Management**: Fluent UI Button components handle focus states

### HamburgerMenu
- **Keyboard Navigation**: Menu fully keyboard accessible (Tab, Enter, Arrow keys)
- **ARIA Labels**: `aria-label="Menu"` on menu trigger button
- **Fluent UI Menu**: Uses native accessibility features from `@fluentui/react-components`
- **Focus Management**: Menu automatically manages focus when opening/closing

### Adaptive Cards
- **Theme Inheritance**: Cards inherit dark mode color tokens for proper contrast
- **Transparent Backgrounds**: Prevents contrast issues with parent background
- **Fluent UI Tokens**: Uses design system tokens for consistent accessible colors

## Testing Accessibility

### During Development
1. **Enable Runtime Testing**:
   ```bash
   # Add to web/chat/.env
   VITE_A11Y=true
   ```

2. **Start Development Server**:
   ```bash
   cd web/chat
   npm run dev
   ```

3. **Check Browser Console**: Axe-core will log accessibility violations with:
   - Severity level (critical, serious, moderate, minor)
   - Rule violated
   - Affected elements
   - Remediation guidance

### Static Analysis
```bash
cd web/chat
npm run lint
```

This checks for accessibility issues during development and CI/CD builds.

## Keyboard Navigation

### Global
- **Tab**: Navigate between interactive elements
- **Enter/Space**: Activate buttons and links
- **Escape**: Close menus and dialogs

### Project Carousel
- **Tab**: Focus on prev/next buttons
- **Enter/Space**: Navigate between projects

### Hamburger Menu
- **Tab**: Focus on menu button
- **Enter/Space**: Open menu
- **Arrow Up/Down**: Navigate menu items
- **Enter**: Select menu item
- **Escape**: Close menu

## Screen Reader Support

### Announcements
- Project carousel updates are announced via `aria-live="polite"`
- Menu state changes are announced by Fluent UI Menu component
- Button states (disabled/enabled) are announced automatically

### Content Structure
- Proper heading hierarchy (`<h1>`, `<h2>`, `<h3>`)
- Semantic HTML for landmarks (`<main>`, `<header>`, `<nav>`)
- ARIA roles for custom components (`role="region"`, `role="group"`)

## Color Contrast

All components use Fluent UI design tokens which ensure WCAG 2.1 AA contrast ratios:
- Normal text: 4.5:1 minimum
- Large text (18pt+): 3:1 minimum
- UI components: 3:1 minimum

## Known Limitations

1. **Adaptive Cards Library**: The adaptivecards library v3.0.5 has limited accessibility support. We've mitigated this by:
   - Building custom React components (ProjectCarousel) instead of using Adaptive Cards Carousel
   - Using Fluent UI components which have full accessibility support

2. **TypeScript `any` Types**: Some components use `any` types for Adaptive Cards payloads due to library type limitations. These are warnings only and don't affect accessibility.

## Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Fluent UI Accessibility](https://react.fluentui.dev/?path=/docs/concepts-developer-accessibility--page)
- [Axe-core Documentation](https://github.com/dequelabs/axe-core)
- [ESLint Plugin JSX A11y](https://github.com/jsx-eslint/eslint-plugin-jsx-a11y)
