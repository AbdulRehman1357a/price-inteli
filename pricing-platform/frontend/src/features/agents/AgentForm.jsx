import { zodResolver } from "@hookform/resolvers/zod";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Checkbox from "@mui/material/Checkbox";
import FormControlLabel from "@mui/material/FormControlLabel";
import Grid from "@mui/material/Grid";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";

import CategorySelect from "../categories/CategorySelect";
import ProductMultiSelect from "../pricing/ProductMultiSelect";
import StoreSelect from "../stores/StoreSelect";
import { usePolicies, useUpdatePolicy } from "./hooks";
import {
  AGENT_STATUS_OPTIONS,
  AGENT_TYPE_OPTIONS,
  IMPLEMENTED_AGENT_TYPES,
  POLICY_MODE_OPTIONS,
  SCHEDULE_OPTIONS,
  SCOPE_OPTIONS,
} from "./options";
import { agentSchema } from "./validation";

const EMPTY_VALUES = {
  name: "",
  agentType: "pricing_optimization",
  status: "active",
  schedule: "manual",
  scope: "all",
  categoryId: "",
  storeId: "",
  productIds: [],
  maxProductsPerRun: 50,
  mode: "recommendation_only",
  minConfidence: 0.7,
  maxPriceChangePercent: 10,
  minMarginPercent: 15,
  approvalRequired: true,
};

export default function AgentForm({ mode, defaultValues, onSubmitAgent, submitLabel }) {
  const isEdit = mode === "edit";
  const [formError, setFormError] = useState(null);
  const { data: policies } = usePolicies();
  const updatePolicy = useUpdatePolicy();

  const {
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(agentSchema),
    defaultValues: { ...EMPTY_VALUES, ...defaultValues },
  });

  const agentType = watch("agentType");
  const scope = watch("scope");

  // On create, pre-fill the policy fields from the shared policy already
  // configured for whichever agent type is selected — every agent of the
  // same type in this organization shares one policy (ai_policies has no
  // agent_id column; see the AIPolicy model docstring).
  useEffect(() => {
    if (isEdit || !policies) return;
    const policy = policies.find((p) => p.agent_type === agentType);
    if (!policy) return;
    setValue("mode", policy.mode);
    setValue("minConfidence", Number(policy.min_confidence));
    setValue("maxPriceChangePercent", Number(policy.max_price_change_percent));
    setValue("minMarginPercent", Number(policy.min_margin_percent));
    setValue("approvalRequired", policy.approval_required);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agentType, policies, isEdit]);

  const submit = async (values) => {
    setFormError(null);
    try {
      await onSubmitAgent(values);
      await updatePolicy.mutateAsync({
        agentType: values.agentType,
        payload: {
          mode: values.mode,
          min_confidence: String(values.minConfidence),
          max_price_change_percent: String(values.maxPriceChangePercent),
          min_margin_percent: String(values.minMarginPercent),
          approval_required: values.approvalRequired,
          auto_execute: values.mode === "auto_execute_within_limits" && !values.approvalRequired,
        },
      });
    } catch (error) {
      setFormError(error.response?.data?.error?.message ?? "Unable to save this agent. Please try again.");
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit(submit)} noValidate>
      <Stack spacing={3}>
        {formError && <Alert severity="error">{formError}</Alert>}

        <section>
          <Typography variant="subtitle1" gutterBottom>
            Agent
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Controller
                name="name"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Agent Name"
                    required
                    fullWidth
                    error={!!errors.name}
                    helperText={errors.name?.message}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="agentType"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    select
                    label="Agent Type"
                    required
                    fullWidth
                    disabled={isEdit}
                    helperText={
                      !IMPLEMENTED_AGENT_TYPES.has(field.value)
                        ? "Not implemented yet — running this agent will fail."
                        : undefined
                    }
                  >
                    {AGENT_TYPE_OPTIONS.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="status"
                control={control}
                render={({ field }) => (
                  <TextField {...field} select label="Status" required fullWidth>
                    {AGENT_STATUS_OPTIONS.map((option) => (
                      <MenuItem key={option} value={option}>
                        {option}
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="schedule"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    select
                    label="Schedule"
                    required
                    fullWidth
                    helperText="Runs are triggered manually in this release regardless of schedule."
                  >
                    {SCHEDULE_OPTIONS.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
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
            Scope
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={4}>
              <Controller
                name="scope"
                control={control}
                render={({ field }) => (
                  <TextField {...field} select label="Products to Evaluate" fullWidth>
                    {SCOPE_OPTIONS.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />
            </Grid>
            {scope === "category" && (
              <Grid item xs={12} sm={4}>
                <Controller
                  name="categoryId"
                  control={control}
                  render={({ field }) => <CategorySelect value={field.value} onChange={field.onChange} />}
                />
              </Grid>
            )}
            {scope === "products" && (
              <Grid item xs={12} sm={8}>
                <Controller
                  name="productIds"
                  control={control}
                  render={({ field }) => (
                    <ProductMultiSelect
                      value={field.value.map((id) => ({ id }))}
                      onChange={(products) => field.onChange(products.map((p) => p.id))}
                      label="Products"
                    />
                  )}
                />
              </Grid>
            )}
            <Grid item xs={12} sm={4}>
              <Controller
                name="storeId"
                control={control}
                render={({ field }) => (
                  <StoreSelect
                    value={field.value}
                    onChange={field.onChange}
                    label="Store (optional — org-wide if blank)"
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <Controller
                name="maxProductsPerRun"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    type="number"
                    label="Maximum Products Per Run"
                    fullWidth
                    error={!!errors.maxProductsPerRun}
                    helperText={errors.maxProductsPerRun?.message}
                  />
                )}
              />
            </Grid>
          </Grid>
        </section>

        <section>
          <Typography variant="subtitle1" gutterBottom>
            Execution Policy
          </Typography>
          <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
            Shared by every {AGENT_TYPE_OPTIONS.find((o) => o.value === agentType)?.label ?? "agent"} in your
            organization. Guardrails (minimum margin, price bounds from pricing rules) still apply
            regardless of this policy — an agent can never bypass them.
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Controller
                name="mode"
                control={control}
                render={({ field }) => (
                  <TextField {...field} select label="Execution Mode" required fullWidth>
                    {POLICY_MODE_OPTIONS.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="approvalRequired"
                control={control}
                render={({ field }) => (
                  <FormControlLabel
                    control={<Checkbox checked={field.value} onChange={field.onChange} />}
                    label="Approval Required (overrides auto-execute if checked)"
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <Controller
                name="minConfidence"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    type="number"
                    label="Confidence Threshold (0-1)"
                    fullWidth
                    inputProps={{ step: 0.01, min: 0, max: 1 }}
                    error={!!errors.minConfidence}
                    helperText={errors.minConfidence?.message}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <Controller
                name="maxPriceChangePercent"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    type="number"
                    label="Maximum Price Change (%)"
                    fullWidth
                    error={!!errors.maxPriceChangePercent}
                    helperText={errors.maxPriceChangePercent?.message}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <Controller
                name="minMarginPercent"
                control={control}
                render={({ field }) => (
                  <TextField {...field} type="number" label="Minimum Margin (%)" fullWidth />
                )}
              />
            </Grid>
          </Grid>
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
