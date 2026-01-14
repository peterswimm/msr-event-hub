import React, { useState } from "react";
import { Button, Card, Text, makeStyles, tokens } from "@fluentui/react-components";
import { ChevronLeft24Regular, ChevronRight24Regular } from "@fluentui/react-icons";

const useStyles = makeStyles({
  container: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    maxWidth: "600px",
  },
  header: {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  },
  title: {
    fontSize: tokens.fontSizeBase500,
    fontWeight: tokens.fontWeightSemibold,
  },
  subtitle: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorBrandForeground1,
  },
  carouselWrapper: {
    position: "relative",
    overflow: "hidden",
  },
  carouselContent: {
    display: "flex",
    transition: "transform 0.3s ease-in-out",
  },
  projectCard: {
    minWidth: "100%",
    padding: "16px",
    boxSizing: "border-box",
  },
  projectTitle: {
    fontSize: tokens.fontSizeBase400,
    fontWeight: tokens.fontWeightSemibold,
    marginBottom: "4px",
  },
  projectArea: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorBrandForeground1,
    marginBottom: "12px",
  },
  projectDescription: {
    fontSize: tokens.fontSizeBase300,
    lineHeight: "1.5",
    marginBottom: "12px",
  },
  projectTeam: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
  },
  controls: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: "12px",
  },
  navButtons: {
    display: "flex",
    gap: "8px",
  },
  counter: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
  },
  actions: {
    display: "flex",
    gap: "8px",
    flexWrap: "wrap",
    marginTop: "12px",
  },
});

interface Project {
  name: string;
  researchArea?: string;
  description?: string;
  team?: Array<{ displayName?: string; name?: string }>;
}

interface ProjectCarouselProps {
  title?: string;
  subtitle?: string;
  projects: Project[];
  actions?: Array<{ title: string; data: any }>;
  onAction?: (data: any) => void;
}

const ProjectCarousel: React.FC<ProjectCarouselProps> = ({
  title = "Projects",
  subtitle,
  projects,
  actions,
  onAction,
}) => {
  const styles = useStyles();
  const [currentIndex, setCurrentIndex] = useState(0);

  const handlePrevious = () => {
    setCurrentIndex((prev) => (prev > 0 ? prev - 1 : projects.length - 1));
  };

  const handleNext = () => {
    setCurrentIndex((prev) => (prev < projects.length - 1 ? prev + 1 : 0));
  };

  const handleActionClick = (actionData: any) => {
    if (onAction) {
      onAction(actionData);
    }
  };

  if (!projects || projects.length === 0) {
    return <Text>No projects available</Text>;
  }

  const currentProject = projects[currentIndex];
  const teamText = currentProject.team
    ?.map((m) => m.displayName || m.name || "")
    .filter(Boolean)
    .join(", ") || "No team info";

  return (
    <div className={styles.container} role="region" aria-label="Project carousel">
      <div className={styles.header}>
        <Text className={styles.title}>{title}</Text>
        {subtitle && <Text className={styles.subtitle}>{subtitle}</Text>}
      </div>

      <Card className={styles.carouselWrapper}>
        <div
          className={styles.carouselContent}
          style={{ transform: `translateX(-${currentIndex * 100}%)` }}
          role="group"
          aria-live="polite"
        >
          {projects.map((project, idx) => (
            <div key={idx} className={styles.projectCard}>
              <Text className={styles.projectTitle} as="h3">
                {project.name || "Untitled Project"}
              </Text>
              {project.researchArea && (
                <Text className={styles.projectArea}>{project.researchArea}</Text>
              )}
              <Text className={styles.projectDescription}>
                {project.description?.slice(0, 200) || "Description unavailable"}
                {(project.description?.length || 0) > 200 && "..."}
              </Text>
              <Text className={styles.projectTeam}>👥 {teamText}</Text>
            </div>
          ))}
        </div>

        <div className={styles.controls}>
          <div className={styles.navButtons}>
            <Button
              appearance="subtle"
              icon={<ChevronLeft24Regular />}
              onClick={handlePrevious}
              disabled={projects.length <= 1}
              aria-label="Previous project"
            />
            <Button
              appearance="subtle"
              icon={<ChevronRight24Regular />}
              onClick={handleNext}
              disabled={projects.length <= 1}
              aria-label="Next project"
            />
          </div>
          <Text className={styles.counter}>
            {currentIndex + 1} of {projects.length}
          </Text>
        </div>
      </Card>

      {actions && actions.length > 0 && (
        <div className={styles.actions}>
          {actions.map((action, idx) => (
            <Button
              key={idx}
              appearance={idx === 0 ? "primary" : "secondary"}
              onClick={() => handleActionClick(action.data)}
            >
              {action.title}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
};

export default ProjectCarousel;
