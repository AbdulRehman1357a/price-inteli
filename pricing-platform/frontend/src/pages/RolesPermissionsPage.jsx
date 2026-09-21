import EditIcon from "@mui/icons-material/Edit";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import Accordion from "@mui/material/Accordion";
import AccordionDetails from "@mui/material/AccordionDetails";
import AccordionSummary from "@mui/material/AccordionSummary";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useState } from "react";

import { useAuth } from "../features/auth/AuthContext";
import { useRoles } from "../features/roles/hooks";
import RolePermissionsEditDialog from "../features/roles/RolePermissionsEditDialog";

function groupByModule(permissions) {
  const groups = {};
  for (const permission of permissions) {
    groups[permission.module] ??= [];
    groups[permission.module].push(permission);
  }
  return groups;
}

export default function RolesPermissionsPage() {
  const { data: roles, isLoading, isError } = useRoles();
  const { hasPermission } = useAuth();
  const [editingRole, setEditingRole] = useState(null);
  const canEdit = hasPermission("users.update");

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Roles &amp; Permissions
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Reference of the system roles and what each one grants. Assign roles to a user from the Users
        screen{canEdit && ", or edit a role's permissions below to customize it for your organization"}.
      </Typography>

      {isLoading && (
        <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
          <CircularProgress />
        </Box>
      )}

      {isError && <Alert severity="error">Unable to load roles.</Alert>}

      {roles?.map((role) => {
        const groups = groupByModule(role.permissions);
        return (
          <Accordion key={role.id} variant="outlined" disableGutters>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Stack direction="row" spacing={1.5} alignItems="center">
                <Typography variant="subtitle1">{role.name}</Typography>
                <Chip label={`${role.permissions.length} permissions`} size="small" variant="outlined" />
                {!role.is_system_role && <Chip label="Customized" size="small" color="primary" />}
              </Stack>
            </AccordionSummary>
            <AccordionDetails>
              {role.description && (
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {role.description}
                </Typography>
              )}
              {role.permissions.length === 0 && (
                <Typography variant="body2" color="text.secondary">
                  This role has no permissions.
                </Typography>
              )}
              <Stack spacing={1.5} sx={{ mb: canEdit ? 2 : 0 }}>
                {Object.entries(groups).map(([module, permissions]) => (
                  <Box key={module}>
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5 }}>
                      {module}
                    </Typography>
                    <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                      {permissions.map((permission) => (
                        <Chip key={permission.id} label={permission.code} size="small" />
                      ))}
                    </Stack>
                  </Box>
                ))}
              </Stack>
              {canEdit && (
                <Button size="small" startIcon={<EditIcon />} onClick={() => setEditingRole(role)}>
                  Edit Permissions
                </Button>
              )}
            </AccordionDetails>
          </Accordion>
        );
      })}

      <RolePermissionsEditDialog
        open={Boolean(editingRole)}
        role={editingRole}
        onClose={() => setEditingRole(null)}
      />
    </Container>
  );
}
