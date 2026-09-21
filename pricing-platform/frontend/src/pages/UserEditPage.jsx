import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import { useNavigate, useParams } from "react-router-dom";

import UserForm from "../features/users/UserForm";
import { useUpdateUser, useUser } from "../features/users/hooks";

export default function UserEditPage() {
  const { userId } = useParams();
  const navigate = useNavigate();
  const { data: user, isLoading, isError } = useUser(userId);
  const updateUser = useUpdateUser(userId);

  const handleSubmit = async (values) => {
    await updateUser.mutateAsync(values);
    navigate("/users", { replace: true });
  };

  if (isLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError || !user) {
    return (
      <Container sx={{ py: 4 }}>
        <Alert severity="error">User not found.</Alert>
      </Container>
    );
  }

  const defaultValues = {
    firstName: user.first_name,
    lastName: user.last_name,
    email: user.email,
    phone: user.phone ?? "",
    status: user.status,
    roleIds: user.roles.map((role) => role.id),
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Edit User
      </Typography>
      <Paper variant="outlined" sx={{ p: 3, mt: 2 }}>
        <UserForm mode="edit" defaultValues={defaultValues} onSubmit={handleSubmit} submitLabel="Save Changes" />
      </Paper>
    </Container>
  );
}
