import { zodResolver } from "@hookform/resolvers/zod";
import DeleteIcon from "@mui/icons-material/Delete";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Grid from "@mui/material/Grid";
import IconButton from "@mui/material/IconButton";
import MenuItem from "@mui/material/MenuItem";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";

import { useCreateMapping, useDeleteMapping, useMappings } from "./hooks";
import { ENTITY_TYPE_OPTIONS, TRANSFORMATION_OPTIONS } from "./options";
import { mappingSchema } from "./validation";

const transformationLabel = (value) =>
  TRANSFORMATION_OPTIONS.find((o) => o.value === value)?.label ?? value ?? "Direct (no change)";

export default function MappingsTable({ integrationId }) {
  const [formError, setFormError] = useState(null);
  const { data: mappings, isLoading } = useMappings(integrationId);
  const createMapping = useCreateMapping(integrationId);
  const deleteMapping = useDeleteMapping(integrationId);

  const {
    control,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(mappingSchema),
    defaultValues: { entity_type: "product", source_field: "", canonical_field: "", transformation_rule: "" },
  });

  const submit = async (values) => {
    setFormError(null);
    try {
      await createMapping.mutateAsync({
        entity_type: values.entity_type,
        source_field: values.source_field,
        canonical_field: values.canonical_field,
        transformation_rule: values.transformation_rule || null,
      });
      reset({ entity_type: values.entity_type, source_field: "", canonical_field: "", transformation_rule: "" });
    } catch (error) {
      setFormError(error.response?.data?.error?.message ?? "Unable to add this mapping.");
    }
  };

  return (
    <Stack spacing={3}>
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          Add Field Mapping
        </Typography>
        {formError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {formError}
          </Alert>
        )}
        <Box component="form" onSubmit={handleSubmit(submit)} noValidate>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={2}>
              <Controller
                name="entity_type"
                control={control}
                render={({ field }) => (
                  <TextField {...field} select label="Entity" fullWidth>
                    {ENTITY_TYPE_OPTIONS.map((option) => (
                      <MenuItem key={option} value={option}>
                        {option}
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <Controller
                name="source_field"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Source Field"
                    required
                    fullWidth
                    error={!!errors.source_field}
                    helperText={errors.source_field?.message}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <Controller
                name="canonical_field"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Canonical Field"
                    required
                    fullWidth
                    error={!!errors.canonical_field}
                    helperText={errors.canonical_field?.message}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <Controller
                name="transformation_rule"
                control={control}
                render={({ field }) => (
                  <TextField {...field} select label="Transformation" fullWidth>
                    {TRANSFORMATION_OPTIONS.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />
            </Grid>
            <Grid item xs={12} sm={1}>
              <Button type="submit" variant="contained" fullWidth disabled={isSubmitting}>
                Add
              </Button>
            </Grid>
          </Grid>
        </Box>
      </Paper>

      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Entity</TableCell>
              <TableCell>Source Field</TableCell>
              <TableCell>Canonical Field</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Transformation</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {!isLoading && (mappings ?? []).length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                  <Typography color="text.secondary">No field mappings configured yet.</Typography>
                </TableCell>
              </TableRow>
            )}
            {(mappings ?? []).map((mapping) => (
              <TableRow key={mapping.id}>
                <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                  {mapping.entity_type}
                </TableCell>
                <TableCell>{mapping.source_field}</TableCell>
                <TableCell>{mapping.canonical_field}</TableCell>
                <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                  {transformationLabel(mapping.transformation_rule)}
                </TableCell>
                <TableCell align="right">
                  <IconButton size="small" onClick={() => deleteMapping.mutate(mapping.id)}>
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Stack>
  );
}
