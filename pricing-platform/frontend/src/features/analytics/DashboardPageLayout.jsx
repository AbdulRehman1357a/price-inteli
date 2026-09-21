import Alert from "@mui/material/Alert";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Grid from "@mui/material/Grid";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useState } from "react";

import DashboardFilters from "./DashboardFilters";
import MetricCard from "./MetricCard";
import { useDashboardMetrics } from "./hooks";
import { defaultDateRange } from "./options";

// Shared shell for every Phase 15 sub-dashboard (Executive/Pricing/
// Inventory/AI/Device) — pages differ only in title/description and which
// metric cards they show; all filtering/fetching logic lives here so page
// components stay thin, per this project's frontend conventions.
export default function DashboardPageLayout({ title, description, cards }) {
  const [filters, setFilters] = useState({ ...defaultDateRange(), storeId: "", categoryId: "", productId: "" });
  const { data, isLoading, isError } = useDashboardMetrics(filters);

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        {title}
      </Typography>
      {description && (
        <Typography color="text.secondary" sx={{ mb: 3 }}>
          {description}
        </Typography>
      )}

      <DashboardFilters {...filters} onChange={setFilters} />

      {isError && <Alert severity="error" sx={{ mb: 2 }}>Unable to load dashboard metrics.</Alert>}
      {data?.is_partial && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Part of this date range hasn't finished calculating yet — it's running in the background and
          these numbers will fill in on a refresh.
        </Alert>
      )}

      {isLoading && !data ? (
        <Stack alignItems="center" sx={{ py: 6 }}>
          <CircularProgress />
        </Stack>
      ) : (
        <Grid container spacing={2}>
          {cards.map((card) => (
            <Grid item xs={12} sm={6} md={3} key={card.metricKey}>
              <MetricCard
                icon={card.icon}
                metricKey={card.metricKey}
                value={data?.[card.metricKey]}
                color={card.color}
              />
            </Grid>
          ))}
        </Grid>
      )}
    </Container>
  );
}
