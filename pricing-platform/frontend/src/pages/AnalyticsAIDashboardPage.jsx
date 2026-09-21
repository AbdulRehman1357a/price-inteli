import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import ThumbUpIcon from "@mui/icons-material/ThumbUp";

import DashboardPageLayout from "../features/analytics/DashboardPageLayout";

const CARDS = [
  { metricKey: "ai_recommendations_count", icon: <AutoAwesomeIcon />, color: "secondary" },
  { metricKey: "ai_approval_rate_pct", icon: <ThumbUpIcon />, color: "success" },
];

export default function AnalyticsAIDashboardPage() {
  return (
    <DashboardPageLayout
      title="AI Dashboard"
      description="How many pricing recommendations the AI is generating, and how often they're approved."
      cards={CARDS}
    />
  );
}
