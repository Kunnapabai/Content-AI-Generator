# Specification Template: Custom About Us Page Template for SuperBank Theme

## 1. High-Level Objective

Create a custom WordPress page template for the "About Us" page that matches the provided SVG design (`gemini.svg`), integrating with the existing SuperBank theme's header and footer while implementing all custom sections with proper styling, responsive design, and ACF fields for content management.

## 2. Mid-Level Objectives

*   **Create Page Template File**: Set up `page-about-us.php` template that uses existing theme header/footer
*   **Implement Hero Section**: Gradient purple/blue hero with centered content, pill badge, title, subtitle, and CTA button
*   **Implement "Our Meaning" Section**: Two-column layout with left image and right content explaining Housecoach and "102" code
*   **Implement "Consultation Contexts" Section**: Three-card grid on gray background showcasing Family, Career, and Health contexts
*   **Implement "Self-Discovery" Section**: Two-column layout with left content (including quote block) and right image
*   **Implement "Key Success Factors" Section**: 2x2 grid with colored boxes for Goals, Determination, Skills, and Success
*   **Create CSS Styles**: Add dedicated stylesheet with all section styles, colors, typography, and responsive breakpoints
*   **Set Up ACF Fields**: Create Advanced Custom Fields for all editable content (optional but recommended)

## 3. Implementation Notes & Constraints

### Technical Requirements
- **Theme**: SuperBank (WordPress theme in `/wp-content/themes/superbank/`)
- **PHP Version**: Compatible with existing theme PHP version
- **CSS**: Use existing theme conventions; add new styles in dedicated file or inline
- **Fonts**: Use Inter font family (already imported via Google Fonts in design)
- **Responsive**: Must be mobile-friendly with appropriate breakpoints

### Design Specifications (from SVG)
- **Primary Brand Color**: `#1d4ed8` (blue)
- **Hero Gradient**: `#4c2fed` to `#4361ee` (purple to blue)
- **CTA Button**: `#ffcc00` (yellow) with black text
- **Section Background (gray)**: `#f3f4f6`
- **Footer Background**: `#2545a8` (already exists in theme)
- **Text Colors**:
  - Headings: `#0f172a`, `#1f2937`
  - Body: `#475569`, `#6b7280`
  - Labels: `#1d4ed8` (blue)

### Constraints
- Do NOT modify existing header (`header.php`) or footer (`footer.php`)
- Follow existing theme coding patterns and naming conventions
- Ensure no conflicts with existing theme styles
- Images will use placeholder boxes initially (to be replaced with real images)

## 4. Low-Level Tasks (Ordered Steps)

### Phase 1: Template Setup

1. **Create the page template file**
   - Create `/wp-content/themes/superbank/templates/page-about-us.php`
   - Add WordPress template header comment: `/* Template Name: About Us */`
   - Include `get_header()` and `get_footer()` calls
   - Set up main content wrapper with unique class `.about-us-page`

2. **Create dedicated CSS file**
   - Create `/wp-content/themes/superbank/assets/css/page-about-us.css`
   - Add CSS reset/base styles for the page
   - Enqueue stylesheet in `functions.php` conditionally for this template

### Phase 2: Hero Section

3. **Build Hero Section HTML structure**
   ```
   - Container with gradient background
   - Centered content wrapper (max-width: ~800px)
   - Pill badge "About Us"
   - H1 title: "Housecoach102 Story & Vision"
   - Subtitle paragraph (3 lines)
   - CTA button "Learn More"
   ```

4. **Style Hero Section**
   - Linear gradient background: `linear-gradient(90deg, #4c2fed, #4361ee)`
   - Min-height: ~600px
   - Center all content vertically and horizontally
   - Pill badge: semi-transparent white bg with white border, white text
   - Typography: Title 56px bold, Subtitle 18px regular
   - CTA: Yellow bg (#ffcc00), 8px border-radius, black bold text

### Phase 3: "Our Meaning" Section

5. **Build "Our Meaning" Section HTML**
   ```
   - Two-column flex container
   - Left: Image placeholder (500x380px, 20px border-radius)
   - Right: Content block
     - Label "OUR MEANING" (blue, small caps)
     - H2 "What is Housecoach?"
     - Description paragraph
     - H3 "The Code 102"
     - Description paragraph
   ```

6. **Style "Our Meaning" Section**
   - Padding: 80px vertical
   - Two-column layout: 50/50 split with gap
   - Decorative background blob (light blue circle, optional)
   - Label: `#1d4ed8`, 14px, font-weight 600
   - H2: `#0f172a`, 40px, font-weight 700
   - Paragraphs: `#475569`, 18px, line-height 1.6

### Phase 4: "Consultation Contexts" Section

7. **Build "Consultation Contexts" Section HTML**
   ```
   - Full-width container with gray background
   - Section header (centered title + subtitle)
   - Three-column card grid
   - Each card:
     - Image area (colored placeholder)
     - Content area with title + description
   ```

8. **Style "Consultation Contexts" Section**
   - Background: `#f3f4f6`
   - Padding: 80px vertical
   - Title: `#1f2937`, 42px, centered
   - Subtitle: `#6b7280`, 18px, centered
   - Cards: white background, 8px border-radius, subtle shadow
   - Card image areas: 200px height with themed colors
     - Family: `#dbeafe`
     - Career: `#e0e7ff`
     - Health: `#fae8ff`
   - Card titles: 24px bold
   - Card descriptions: 16px regular, gray

### Phase 5: "Self-Discovery" Section

9. **Build "Self-Discovery" Section HTML**
   ```
   - Two-column flex container (reversed order)
   - Left: Content block
     - Label "CORE PHILOSOPHY"
     - H2 "The Importance of Self-Discovery"
     - Description paragraph
     - Quote block with yellow accent bar
   - Right: Image placeholder (500x400px)
   ```

10. **Style "Self-Discovery" Section**
    - Padding: 80px vertical
    - Quote block: 4px yellow left border, italic text, indented
    - Same typography patterns as "Our Meaning" section

### Phase 6: "Key Success Factors" Section

11. **Build "Key Success Factors" Section HTML**
    ```
    - Section header (centered title)
    - 2x2 grid layout
    - Four boxes:
      - Goals (amber theme)
      - Determination (blue theme)
      - Skills & Potential (green theme)
      - Success (purple theme)
    - Each box: colored background, title, description
    ```

12. **Style "Key Success Factors" Section**
    - Padding: 80px vertical
    - Grid: 2 columns, gap 60px horizontal, 40px vertical
    - Box styles:
      - Goals: bg `#fffbeb`, border `#fef3c7`, title `#b45309`
      - Determination: bg `#eff6ff`, border `#dbeafe`, title `#1e40af`
      - Skills: bg `#f0fdf4`, border `#dcfce7`, title `#15803d`
      - Success: bg `#faf5ff`, border `#f3e8ff`, title `#7e22ce`
    - Box padding: 30px, border-radius: 12px
    - Box dimensions: ~560x180px

### Phase 7: Responsive Design

13. **Add tablet breakpoint styles (max-width: 1024px)**
    - Hero: Reduce title size to 42px
    - Two-column sections: Stack vertically
    - Three-card grid: 2 columns or stack
    - 2x2 grid: Single column

14. **Add mobile breakpoint styles (max-width: 768px)**
    - Hero: Title 32px, subtitle 16px, padding reduced
    - All sections: Single column layouts
    - Cards: Full width, reduced padding
    - Adjust all font sizes proportionally

### Phase 8: Integration & Testing

15. **Enqueue styles in functions.php**
    - Add conditional enqueue for `page-about-us.css`
    - Ensure proper load order (after main theme styles)

16. **Create WordPress page**
    - Create new page in WordPress admin
    - Set page title to "About Us"
    - Select "About Us" template from Page Attributes
    - Set appropriate slug (e.g., `/about-us`)

17. **Test and refine**
    - Test on desktop, tablet, and mobile viewports
    - Verify no conflicts with existing theme styles
    - Check header/footer integration
    - Validate HTML and CSS

### Phase 9: Optional Enhancements

18. **Add ACF fields for content management (optional)**
    - Create field group for About Us page
    - Add fields for: hero content, section texts, images, quotes
    - Update template to use ACF field values

19. **Add subtle animations (optional)**
    - Fade-in on scroll for sections
    - Hover effects on cards and buttons

---

## File Structure Summary

```
wp-content/themes/superbank/
├── templates/
│   └── page-about-us.php          # New template file
├── assets/
│   └── css/
│       └── page-about-us.css      # New stylesheet
└── functions.php                   # Add style enqueue
```

## Color Reference

| Element | Color Code |
|---------|------------|
| Hero Gradient Start | `#4c2fed` |
| Hero Gradient End | `#4361ee` |
| CTA Button | `#ffcc00` |
| Primary Blue | `#1d4ed8` |
| Heading Dark | `#0f172a` |
| Body Text | `#475569` |
| Gray Background | `#f3f4f6` |
| White | `#ffffff` |

## Execution Status

Completed
- Created `wp-content/themes/superbank/templates/page-about-us.php` with all sections and placeholder content.
- Added `wp-content/themes/superbank/assets/css/page-about-us.css` with full layout styling, responsive breakpoints, and animations.
- Enqueued the About Us stylesheet and Inter font conditionally in `wp-content/themes/superbank/functions.php`.

Pending
- Create the WordPress page and assign the About Us template.
- Validate layout across desktop/tablet/mobile in the browser.
- Optional: ACF fields for editable content.
- Optional: Scroll/fade animation triggers beyond CSS (if desired).
