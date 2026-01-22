/**
 * Automated Accessibility Tests for Adaptive Card Components
 * Tests WCAG 2.1 AA compliance using axe-core
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import AdaptiveCardRenderer from '../components/AdaptiveCardRenderer';
import ProjectCarousel from '../components/ProjectCarousel';

// Extend expect with jest-axe matchers
expect.extend(toHaveNoViolations);

describe('AdaptiveCardRenderer Accessibility', () => {
  it('should render without accessibility violations - welcome card', async () => {
    const welcomeCard = {
      "$schema": "https://adaptivecards.io/schemas/adaptive-card.json",
      "type": "AdaptiveCard",
      "version": "1.5",
      "fallbackText": "Welcome to MSR Event Hub",
      "body": [
        {
          "type": "TextBlock",
          "text": "Welcome!",
          "size": "large",
          "weight": "bolder"
        }
      ]
    };

    const { container } = render(<AdaptiveCardRenderer card={welcomeCard} />);
    const results = await axe(container);
    
    expect(results).toHaveNoViolations();
  });

  it('should render without accessibility violations - project card', async () => {
    const projectCard = {
      "$schema": "https://adaptivecards.io/schemas/adaptive-card.json",
      "type": "AdaptiveCard",
      "version": "1.5",
      "fallbackText": "Research project: AI for Healthcare",
      "body": [
        {
          "type": "TextBlock",
          "text": "AI for Healthcare",
          "size": "large",
          "weight": "bolder"
        },
        {
          "type": "TextBlock",
          "text": "Artificial Intelligence",
          "color": "accent"
        },
        {
          "type": "TextBlock",
          "text": "Using machine learning to improve patient outcomes.",
          "wrap": true
        }
      ],
      "actions": [
        {
          "type": "Action.Submit",
          "title": "Learn More",
          "data": {
            "action": "view_details",
            "projectId": "ai-healthcare-001"
          }
        }
      ]
    };

    const { container } = render(<AdaptiveCardRenderer card={projectCard} />);
    const results = await axe(container);
    
    expect(results).toHaveNoViolations();
  });

  it('should render without accessibility violations - form card', async () => {
    const formCard = {
      "$schema": "https://adaptivecards.io/schemas/adaptive-card.json",
      "type": "AdaptiveCard",
      "version": "1.5",
      "fallbackText": "Feedback form",
      "body": [
        {
          "type": "TextBlock",
          "text": "Feedback Form",
          "size": "large",
          "weight": "bolder"
        },
        {
          "type": "Input.Text",
          "id": "name",
          "label": "Name",
          "placeholder": "Enter your name",
          "isRequired": true,
          "errorMessage": "Name is required"
        },
        {
          "type": "Input.Text",
          "id": "email",
          "label": "Email",
          "placeholder": "your.email@example.com",
          "style": "Email",
          "isRequired": true,
          "errorMessage": "Valid email is required"
        }
      ],
      "actions": [
        {
          "type": "Action.Submit",
          "title": "Submit",
          "data": {
            "action": "submitFeedback"
          }
        }
      ]
    };

    const { container } = render(<AdaptiveCardRenderer card={formCard} />);
    const results = await axe(container);
    
    expect(results).toHaveNoViolations();
  });

  it('should have proper fallbackText for accessibility', () => {
    const cardWithFallback = {
      "$schema": "https://adaptivecards.io/schemas/adaptive-card.json",
      "type": "AdaptiveCard",
      "version": "1.5",
      "fallbackText": "Important project information",
      "body": [
        {
          "type": "TextBlock",
          "text": "Project Details"
        }
      ]
    };

    render(<AdaptiveCardRenderer card={cardWithFallback} />);
    
    // Card should render without errors
    expect(screen.queryByText(/Project Details/i)).toBeTruthy();
  });
});

describe('ProjectCarousel Accessibility', () => {
  const mockProjects = [
    {
      name: "AI Research Project",
      researchArea: "Artificial Intelligence",
      description: "Exploring new frontiers in machine learning and neural networks.",
      team: [
        { displayName: "Dr. Jane Smith" },
        { displayName: "Prof. John Doe" }
      ]
    },
    {
      name: "Quantum Computing Initiative",
      researchArea: "Quantum Systems",
      description: "Advancing quantum algorithms for practical applications.",
      team: [
        { displayName: "Dr. Alice Johnson" }
      ]
    },
    {
      name: "HCI Innovation Lab",
      researchArea: "Human-Computer Interaction",
      description: "Designing intuitive interfaces for augmented reality experiences.",
      team: [
        { displayName: "Dr. Bob Wilson" },
        { displayName: "Dr. Carol Martinez" }
      ]
    }
  ];

  it('should render without accessibility violations', async () => {
    const { container } = render(
      <ProjectCarousel
        title="Research Projects"
        subtitle="Explore cutting-edge research"
        projects={mockProjects}
      />
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have proper ARIA labels for carousel', () => {
    render(
      <ProjectCarousel
        title="Research Projects"
        subtitle="Explore cutting-edge research"
        projects={mockProjects}
      />
    );

    // Check for carousel region
    const carouselRegion = screen.getByRole('region', { name: /Project carousel/i });
    expect(carouselRegion).toBeTruthy();
    
    // Check for navigation controls
    const prevButton = screen.getByRole('button', { name: /Previous project/i });
    const nextButton = screen.getByRole('button', { name: /Next project/i });
    
    expect(prevButton).toBeTruthy();
    expect(nextButton).toBeTruthy();
  });

  it('should have proper heading hierarchy', () => {
    const { container } = render(
      <ProjectCarousel
        title="Research Projects"
        subtitle="Explore cutting-edge research"
        projects={mockProjects}
      />
    );

    // Check for h2 title
    const title = container.querySelector('h2');
    expect(title).toBeTruthy();
    expect(title?.textContent).toBe('Research Projects');
    
    // Check for h3 project titles
    const projectTitles = container.querySelectorAll('h3');
    expect(projectTitles.length).toBeGreaterThan(0);
  });

  it('should have keyboard navigation support', () => {
    render(
      <ProjectCarousel
        title="Research Projects"
        projects={mockProjects}
      />
    );

    const prevButton = screen.getByRole('button', { name: /Previous project/i });
    const nextButton = screen.getByRole('button', { name: /Next project/i });

    // Buttons should be keyboard accessible (not disabled when multiple projects)
    expect(prevButton).not.toBeDisabled();
    expect(nextButton).not.toBeDisabled();
  });

  it('should have live region for announcing slide changes', () => {
    const { container } = render(
      <ProjectCarousel
        title="Research Projects"
        projects={mockProjects}
      />
    );

    // Check for aria-live region
    const liveRegion = container.querySelector('[aria-live="polite"]');
    expect(liveRegion).toBeTruthy();
  });

  it('should disable navigation with single project', () => {
    const singleProject = [mockProjects[0]];
    
    render(
      <ProjectCarousel
        title="Research Projects"
        projects={singleProject}
      />
    );

    const prevButton = screen.getByRole('button', { name: /Previous project/i });
    const nextButton = screen.getByRole('button', { name: /Next project/i });

    // Both buttons should be disabled with only one project
    expect(prevButton).toBeDisabled();
    expect(nextButton).toBeDisabled();
  });

  it('should render action buttons with proper labels', () => {
    const mockActions = [
      { title: "View All Projects", data: { action: "browse_all" } },
      { title: "Filter by Category", data: { action: "category_select" } }
    ];

    render(
      <ProjectCarousel
        title="Research Projects"
        projects={mockProjects}
        actions={mockActions}
      />
    );

    const viewAllButton = screen.getByRole('button', { name: "View All Projects" });
    const filterButton = screen.getByRole('button', { name: "Filter by Category" });

    expect(viewAllButton).toBeTruthy();
    expect(filterButton).toBeTruthy();
  });
});

describe('Color Contrast Accessibility', () => {
  it('should test color contrast for card elements', async () => {
    const colorCard = {
      "$schema": "https://adaptivecards.io/schemas/adaptive-card.json",
      "type": "AdaptiveCard",
      "version": "1.5",
      "fallbackText": "Color contrast test",
      "body": [
        {
          "type": "TextBlock",
          "text": "High Contrast Text",
          "size": "large",
          "weight": "bolder"
        },
        {
          "type": "TextBlock",
          "text": "Accent colored text",
          "color": "accent"
        },
        {
          "type": "TextBlock",
          "text": "Subtle text for secondary information",
          "isSubtle": true
        }
      ]
    };

    const { container } = render(<AdaptiveCardRenderer card={colorCard} />);
    
    // Run axe with color-contrast rules
    const results = await axe(container, {
      rules: {
        'color-contrast': { enabled: true }
      }
    });
    
    expect(results).toHaveNoViolations();
  });
});

describe('Keyboard Navigation', () => {
  it('should support Tab navigation through interactive elements', () => {
    const interactiveCard = {
      "$schema": "https://adaptivecards.io/schemas/adaptive-card.json",
      "type": "AdaptiveCard",
      "version": "1.5",
      "fallbackText": "Interactive card",
      "body": [
        {
          "type": "TextBlock",
          "text": "Action Card"
        }
      ],
      "actions": [
        {
          "type": "Action.Submit",
          "title": "First Action",
          "data": { "id": 1 }
        },
        {
          "type": "Action.Submit",
          "title": "Second Action",
          "data": { "id": 2 }
        },
        {
          "type": "Action.OpenUrl",
          "title": "Learn More",
          "url": "https://example.com"
        }
      ]
    };

    render(<AdaptiveCardRenderer card={interactiveCard} />);
    
    const buttons = screen.getAllByRole('button');
    
    // All buttons should be in tab order (tabindex >= 0)
    buttons.forEach(button => {
      const tabIndex = button.getAttribute('tabindex');
      expect(tabIndex === null || parseInt(tabIndex) >= 0).toBe(true);
    });
  });
});
