import EditIcon from "@mui/icons-material/Edit";
import StorefrontIcon from "@mui/icons-material/Storefront";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Container from "@mui/material/Container";
import Grid from "@mui/material/Grid";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { Link as RouterLink } from "react-router-dom";

import { useAuth } from "../features/auth/AuthContext";
import ProfileEditDialog from "../features/auth/ProfileEditDialog";
import OrganizationEditDialog from "../features/organizations/OrganizationEditDialog";

const USER_STATUS_COLORS = { active: "success", inactive: "default", suspended: "error" };
const ORG_STATUS_COLORS = { active: "success", inactive: "default", suspended: "error" };

function Field({ label, value }) {
  return (
    <Grid item xs={12} sm={6}>
      <Typography variant="caption" color="text.secondary" display="block">
        {label}
      </Typography>
      <Typography>{value || "—"}</Typography>
    </Grid>
  );
}

export default function ProfilePage() {
  const { user, organization, roles, hasPermission } = useAuth();
  const [editingProfile, setEditingProfile] = useState(false);
  const [editingOrganization, setEditingOrganization] = useState(false);

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Profile
      </Typography>

      <Stack spacing={3}>
        <Paper variant="outlined" sx={{ p: 3 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
            <Typography variant="subtitle1" gutterBottom>
              My Account
            </Typography>
            <Button size="small" startIcon={<EditIcon />} onClick={() => setEditingProfile(true)}>
              Edit
            </Button>
          </Stack>
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Field label="Full Name" value={`${user?.first_name ?? ""} ${user?.last_name ?? ""}`.trim()} />
            <Field label="Email" value={user?.email} />
            <Field label="Phone" value={user?.phone} />
            <Field
              label="Status"
              value={
                <Chip
                  label={user?.status}
                  size="small"
                  color={USER_STATUS_COLORS[user?.status] ?? "default"}
                  variant="outlined"
                />
              }
            />
            <Field
              label="Member Since"
              value={user?.created_at ? new Date(user.created_at).toLocaleDateString() : null}
            />
            <Field
              label="Last Login"
              value={user?.last_login_at ? new Date(user.last_login_at).toLocaleString() : "Never"}
            />
          </Grid>
          {roles?.length > 0 && (
            <Box>
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5 }}>
                Roles
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {roles.map((role) => (
                  <Chip key={role} label={role} size="small" />
                ))}
              </Stack>
            </Box>
          )}
        </Paper>

        <Paper variant="outlined" sx={{ p: 3 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
            <Typography variant="subtitle1" gutterBottom>
              Company Details
            </Typography>
            <Stack direction="row" spacing={1}>
              <Button
                size="small"
                startIcon={<StorefrontIcon />}
                component={RouterLink}
                to="/stores"
              >
                Stores
              </Button>
              {hasPermission("organizations.update") && (
                <Button size="small" startIcon={<EditIcon />} onClick={() => setEditingOrganization(true)}>
                  Edit
                </Button>
              )}
            </Stack>
          </Stack>
          <Grid container spacing={2}>
            <Field label="Company Name" value={organization?.name} />
            <Field label="Legal Name" value={organization?.legal_name} />
            <Field label="Email" value={organization?.email} />
            <Field label="Phone" value={organization?.phone} />
            <Field label="Website" value={organization?.website} />
            <Field label="Country" value={organization?.country} />
            <Field label="Timezone" value={organization?.timezone} />
            <Field label="Currency" value={organization?.currency} />
            <Field
              label="Status"
              value={
                <Chip
                  label={organization?.status}
                  size="small"
                  color={ORG_STATUS_COLORS[organization?.status] ?? "default"}
                  variant="outlined"
                />
              }
            />
            <Field
              label="Customer Since"
              value={organization?.created_at ? new Date(organization.created_at).toLocaleDateString() : null}
            />
          </Grid>
        </Paper>
      </Stack>

      <ProfileEditDialog open={editingProfile} onClose={() => setEditingProfile(false)} />
      <OrganizationEditDialog open={editingOrganization} onClose={() => setEditingOrganization(false)} />
    </Container>
  );
}
