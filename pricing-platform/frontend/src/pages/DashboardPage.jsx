import Card from "@mui/material/Card";
import CardActionArea from "@mui/material/CardActionArea";
import CardContent from "@mui/material/CardContent";
import Container from "@mui/material/Container";
import Divider from "@mui/material/Divider";
import Grid from "@mui/material/Grid";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../features/auth/AuthContext";
import { DASHBOARD_CARDS, METRIC_DEFS, formatMetricValue } from "../features/analytics/options";
import { useDashboardMetrics } from "../features/analytics/hooks";

export default function DashboardPage() {
  const { user, hasPermission } = useAuth();
  const navigate = useNavigate();
  const canViewAnalytics = hasPermission("analytics.read");
  // Default trailing-30-day range, no filters; skipped entirely for a role
  // without analytics.read so this page never fires a request that would
  // just come back 403.
  const { data } = useDashboardMetrics({}, { enabled: canViewAnalytics });

  return (
    <Container sx={{ py: 6 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Welcome, {user?.first_name}
      </Typography>

      {canViewAnalytics && (
        <>
          <Typography color="text.secondary" sx={{ mb: 3 }}>
            Trailing 30 days across your organization. Open a dashboard for filters and the full metric set.
          </Typography>
          <Grid container spacing={2}>
            {DASHBOARD_CARDS.map((card) => (
              <Grid item xs={12} sm={6} md={4} key={card.key}>
                <Card variant="outlined" sx={{ height: "100%" }}>
                  <CardActionArea onClick={() => navigate(card.to)} sx={{ height: "100%" }}>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {card.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {card.description}
                      </Typography>
                      <Divider sx={{ mb: 2 }} />
                      <Stack spacing={1}>
                        {card.metrics.map((metricKey) => (
                          <Stack key={metricKey} direction="row" justifyContent="space-between">
                            <Typography variant="body2" color="text.secondary">
                              {METRIC_DEFS[metricKey]?.label ?? metricKey}
                            </Typography>
                            <Typography variant="body2" fontWeight={600}>
                              {formatMetricValue(metricKey, data?.[metricKey])}
                            </Typography>
                          </Stack>
                        ))}
                      </Stack>
                    </CardContent>
                  </CardActionArea>
                </Card>
              </Grid>
            ))}
          </Grid>
        </>
      )}
    </Container>
  );
}
