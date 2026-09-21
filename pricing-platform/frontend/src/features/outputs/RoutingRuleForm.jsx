import { zodResolver } from "@hookform/resolvers/zod";
import Alert from "@mui/material/Alert";
import Autocomplete from "@mui/material/Autocomplete";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Grid from "@mui/material/Grid";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";

import { useAllCategories } from "../categories/hooks";
import ProductMultiSelect from "../pricing/ProductMultiSelect";
import { useAllStores } from "../stores/hooks";
import { OUTPUT_TYPE_OPTIONS, ROUTING_RULE_STATUS_OPTIONS } from "./options";
import { routingRuleSchema } from "./validation";

const EMPTY_VALUES = {
  name: "",
  priority: "100",
  status: "active",
  target_outputs_json: [],
  product_ids: [],
  category_ids: [],
  store_ids: [],
};

// Converts the API's OutputRoutingRuleOut shape (a conditions_json blob)
// into this form's flat field values — same product/category/store scope
// shape as RuleForm.jsx (PricingRule.conditions_json).
export function routingRuleToFormValues(rule, { categories, stores, products }) {
  const conditions = rule.conditions_json ?? {};

  const categoryOptions = (conditions.category_ids ?? [])
    .map((id) => (categories ?? []).find((c) => c.id === id))
    .filter(Boolean);
  const storeOptions = (conditions.store_ids ?? [])
    .map((id) => (stores ?? []).find((s) => s.id === id))
    .filter(Boolean);
  const productOptions = (conditions.product_ids ?? [])
    .map((id) => (products ?? []).find((p) => p.id === id))
    .filter(Boolean);

  return {
    ...EMPTY_VALUES,
    name: rule.name,
    priority: String(rule.priority),
    status: rule.status,
    target_outputs_json: rule.target_outputs_json ?? [],
    product_ids: productOptions,
    category_ids: categoryOptions,
    store_ids: storeOptions,
  };
}

function toApiPayload(values) {
  const conditions_json = {};
  const productIds = (values.product_ids ?? []).map((p) => p.id ?? p);
  const categoryIds = (values.category_ids ?? []).map((c) => c.id ?? c);
  const storeIds = (values.store_ids ?? []).map((s) => s.id ?? s);
  if (productIds.length) conditions_json.product_ids = productIds;
  if (categoryIds.length) conditions_json.category_ids = categoryIds;
  if (storeIds.length) conditions_json.store_ids = storeIds;

  return {
    name: values.name,
    priority: Number(values.priority),
    status: values.status,
    target_outputs_json: values.target_outputs_json,
    conditions_json: Object.keys(conditions_json).length ? conditions_json : null,
  };
}

export default function RoutingRuleForm({ defaultValues, onSubmit, submitLabel }) {
  const [formError, setFormError] = useState(null);
  const { data: categories } = useAllCategories();
  const { data: stores } = useAllStores();

  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(routingRuleSchema),
    defaultValues: { ...EMPTY_VALUES, ...defaultValues },
  });

  const submit = async (values) => {
    setFormError(null);
    try {
      await onSubmit(toApiPayload(values));
    } catch (error) {
      setFormError(error.response?.data?.error?.message ?? "Unable to save this rule. Please try again.");
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit(submit)} noValidate>
      <Stack spacing={3}>
        {formError && <Alert severity="error">{formError}</Alert>}

        <section>
          <Typography variant="subtitle1" gutterBottom>
            Details
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={8}>
              <Controller
                name="name"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Rule Name"
                    required
                    fullWidth
                    error={!!errors.name}
                    helperText={errors.name?.message}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <Controller
                name="priority"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Priority"
                    required
                    fullWidth
                    helperText={errors.priority?.message ?? "Lower runs first"}
                    error={!!errors.priority}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="status"
                control={control}
                render={({ field }) => (
                  <TextField {...field} select label="Status" required fullWidth>
                    {ROUTING_RULE_STATUS_OPTIONS.map((status) => (
                      <MenuItem key={status} value={status}>
                        {status}
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />
            </Grid>
          </Grid>
        </section>

        <section>
          <Typography variant="subtitle1" gutterBottom>
            Condition (If)
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Controller
                name="product_ids"
                control={control}
                render={({ field }) => <ProductMultiSelect value={field.value} onChange={field.onChange} />}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="category_ids"
                control={control}
                render={({ field }) => (
                  <Autocomplete
                    multiple
                    options={categories ?? []}
                    value={field.value}
                    isOptionEqualToValue={(o, v) => o.id === v.id}
                    getOptionLabel={(o) => o.name}
                    onChange={(_, newValue) => field.onChange(newValue)}
                    renderInput={(params) => (
                      <TextField {...params} label="Category Scope" helperText="Leave empty to match any category." />
                    )}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="store_ids"
                control={control}
                render={({ field }) => (
                  <Autocomplete
                    multiple
                    options={stores ?? []}
                    value={field.value}
                    isOptionEqualToValue={(o, v) => o.id === v.id}
                    getOptionLabel={(o) => o.name}
                    onChange={(_, newValue) => field.onChange(newValue)}
                    renderInput={(params) => (
                      <TextField {...params} label="Store Scope" helperText="Leave empty to match any store." />
                    )}
                  />
                )}
              />
            </Grid>
          </Grid>
        </section>

        <section>
          <Typography variant="subtitle1" gutterBottom>
            Target Outputs (Then)
          </Typography>
          <Controller
            name="target_outputs_json"
            control={control}
            render={({ field }) => (
              <Autocomplete
                multiple
                options={OUTPUT_TYPE_OPTIONS.map((o) => o.value)}
                value={field.value}
                getOptionLabel={(value) => OUTPUT_TYPE_OPTIONS.find((o) => o.value === value)?.label ?? value}
                onChange={(_, newValue) => field.onChange(newValue)}
                renderTags={(tagValue, getTagProps) =>
                  tagValue.map((option, index) => (
                    <Chip
                      label={OUTPUT_TYPE_OPTIONS.find((o) => o.value === option)?.label ?? option}
                      {...getTagProps({ index })}
                      key={option}
                    />
                  ))
                }
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Send to"
                    required
                    error={!!errors.target_outputs_json}
                    helperText={errors.target_outputs_json?.message}
                  />
                )}
              />
            )}
          />
        </section>

        <Box>
          <Button type="submit" variant="contained" size="large" disabled={isSubmitting}>
            {submitLabel}
          </Button>
        </Box>
      </Stack>
    </Box>
  );
}
