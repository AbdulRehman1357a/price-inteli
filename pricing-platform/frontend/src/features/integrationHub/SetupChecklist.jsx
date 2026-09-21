import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import RadioButtonUncheckedIcon from "@mui/icons-material/RadioButtonUnchecked";
import Alert from "@mui/material/Alert";
import AlertTitle from "@mui/material/AlertTitle";
import Link from "@mui/material/Link";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";

import { useAuthorities, useLocations, useMappings, useSyncJobs } from "./hooks";

// Onboarding walkthrough shown only while an integration is still `pending`
// (Phase 10 upgrade spec's Integration Wizard steps, condensed into the
// existing tabbed detail page rather than a separate wizard route — see
// this feature's design notes). Each item jumps to the tab that step lives
// in via the page's own tab/setTab state.
export default function SetupChecklist({ integration, onNavigate }) {
  const { data: mappings } = useMappings(integration.id);
  const { data: locations } = useLocations(integration.id);
  const { data: authorities } = useAuthorities(integration.id);
  const { data: jobs } = useSyncJobs(integration.id, { page: 1, pageSize: 1 });

  if (integration.status !== "pending") return null;

  const steps = [
    {
      label: "Test the connection",
      done: Boolean(integration.last_successful_connection_at),
      tab: "overview",
    },
    {
      label: "Discover and map locations",
      done: (locations ?? []).length > 0,
      tab: "locations",
    },
    {
      label: "Configure field mappings",
      done: (mappings ?? []).length > 0,
      tab: "mappings",
    },
    {
      label: "Configure source-of-truth authority (optional)",
      done: (authorities ?? []).length > 0,
      tab: "authority",
    },
    {
      label: "Run an initial sync",
      done: (jobs?.items ?? []).length > 0,
      tab: "jobs",
    },
    {
      label: "Enable webhooks or a schedule (optional)",
      done: integration.has_webhook_secret,
      tab: "webhooks",
    },
  ];

  return (
    <Alert severity="info" icon={false} sx={{ mb: 3 }}>
      <AlertTitle>Setup Checklist</AlertTitle>
      <List dense disablePadding>
        {steps.map((step) => (
          <ListItem key={step.label} disableGutters>
            <ListItemIcon sx={{ minWidth: 32 }}>
              {step.done ? (
                <CheckCircleIcon color="success" fontSize="small" />
              ) : (
                <RadioButtonUncheckedIcon color="disabled" fontSize="small" />
              )}
            </ListItemIcon>
            <ListItemText>
              {step.done ? (
                step.label
              ) : (
                <Link component="button" type="button" onClick={() => onNavigate(step.tab)}>
                  {step.label}
                </Link>
              )}
            </ListItemText>
          </ListItem>
        ))}
      </List>
    </Alert>
  );
}
