import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import { METRIC_DEFS, formatMetricValue } from "./options";

export default function MetricCard({ icon, metricKey, value, color = "primary" }) {
  const label = METRIC_DEFS[metricKey]?.label ?? metricKey;

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Stack direction="row" spacing={2} alignItems="center">
        {icon && (
          <Stack
            sx={{
              width: 44,
              height: 44,
              borderRadius: 2,
              bgcolor: `${color}.main`,
              color: `${color}.contrastText`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            {icon}
          </Stack>
        )}
        <Stack sx={{ minWidth: 0 }}>
          <Typography variant="h5" noWrap>
            {formatMetricValue(metricKey, value)}
          </Typography>
          <Typography variant="body2" color="text.secondary" noWrap>
            {label}
          </Typography>
        </Stack>
      </Stack>
    </Paper>
  );
}
