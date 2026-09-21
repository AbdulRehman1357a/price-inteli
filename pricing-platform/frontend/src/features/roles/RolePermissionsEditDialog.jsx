import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Checkbox from "@mui/material/Checkbox";
import CircularProgress from "@mui/material/CircularProgress";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import FormControlLabel from "@mui/material/FormControlLabel";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useEffect, useState } from "react";

import { usePermissions } from "../permissions/hooks";
import { useUpdateRolePermissions } from "./hooks";

function groupByModule(permissions) {
  const groups = {};
  for (const permission of permissions) {
    groups[permission.module] ??= [];
    groups[permission.module].push(permission);
  }
  return groups;
}

export default function RolePermissionsEditDialog({ open, role, onClose }) {
  const { data: catalog, isLoading } = usePermissions();
  const updatePermissions = useUpdateRolePermissions();
  const [selected, setSelected] = useState(new Set());
  const [formError, setFormError] = useState(null);

  useEffect(() => {
    if (role) {
      setSelected(new Set(role.permissions.map((p) => p.id)));
      setFormError(null);
    }
  }, [role]);

  if (!role) return null;

  const groups = groupByModule(catalog ?? []);

  const toggle = (permissionId) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(permissionId)) next.delete(permissionId);
      else next.add(permissionId);
      return next;
    });
  };

  const toggleModule = (modulePermissions, allSelected) => {
    setSelected((prev) => {
      const next = new Set(prev);
      for (const permission of modulePermissions) {
        if (allSelected) next.delete(permission.id);
        else next.add(permission.id);
      }
      return next;
    });
  };

  const handleSave = async () => {
    setFormError(null);
    try {
      await updatePermissions.mutateAsync({ roleId: role.id, permissionIds: Array.from(selected) });
      onClose();
    } catch (error) {
      setFormError(
        error.response?.data?.error?.message ?? "Unable to save permissions. Please try again."
      );
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>Edit Permissions — {role.name}</DialogTitle>
      <DialogContent>
        <Stack spacing={2}>
          {formError && <Alert severity="error">{formError}</Alert>}
          {role.is_system_role && (
            <Alert severity="info">
              "{role.name}" is a default role shared across organizations. Saving creates a copy
              customized for your organization only — other organizations keep the default.
            </Alert>
          )}

          {isLoading && (
            <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
              <CircularProgress size={28} />
            </Box>
          )}

          {Object.entries(groups).map(([module, permissions]) => {
            const allSelected = permissions.every((p) => selected.has(p.id));
            const someSelected = permissions.some((p) => selected.has(p.id));
            return (
              <Box key={module}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={allSelected}
                      indeterminate={someSelected && !allSelected}
                      onChange={() => toggleModule(permissions, allSelected)}
                    />
                  }
                  label={<Typography variant="subtitle2">{module}</Typography>}
                />
                <Stack sx={{ pl: 4 }}>
                  {permissions.map((permission) => (
                    <FormControlLabel
                      key={permission.id}
                      control={
                        <Checkbox
                          size="small"
                          checked={selected.has(permission.id)}
                          onChange={() => toggle(permission.id)}
                        />
                      }
                      label={permission.name}
                    />
                  ))}
                </Stack>
              </Box>
            );
          })}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={updatePermissions.isPending}>
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={updatePermissions.isPending || selected.size === 0}
        >
          Save Permissions
        </Button>
      </DialogActions>
    </Dialog>
  );
}
