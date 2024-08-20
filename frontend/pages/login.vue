<script setup lang="ts">
  import type { FormSubmitEvent } from '#ui/types'
  import { z } from 'zod'

  const schema = z.object({
    username: z.string().min(1, 'Usuário é obrigatório.'),
    password: z.string().min(5, 'A senha deve ter no mínimo 5 caracteres.'),
  })

  type Schema = z.infer<typeof schema>

  const state = reactive<Schema>({
    username: '',
    password: '',
  })

  const session = useAuth()
  const toast = useToast()
  const isSubmitting = ref(false)
  const noPermissionState = useState('no-permission')

  watch(noPermissionState, () => {
    if (noPermissionState.value) {
      toast.add({
        title: 'Você não tem permissão para acessar esta página',
        description: 'Por favor, entre em sua conta e tente novamente.',
        icon: 'i-clarity-shield-line',
        color: 'red',
        timeout: 2000,
      })

      noPermissionState.value = false
    }
  })

  const onSubmit = async (event: FormSubmitEvent<Schema>) => {
    const { username, password } = event.data

    isSubmitting.value = true
    const success = await session.login(username, password)
    if (success) {
      toast.add({
        title: 'Login realizado com sucesso!',
        description: 'Você será redirecionado em instantes.',
        icon: 'i-clarity-success-standard-line',
        timeout: 2000,
        color: 'green',
      })
      await navigateTo('/')
    } else {
      toast.add({
        title: 'Erro ao efetuar login',
        description: 'Verifique suas credenciais e tente novamente.',
        icon: 'i-clarity-error-line',
        color: 'red',
      })
    }

    isSubmitting.value = false

    state.username = ''
    state.password = ''
  }
</script>

<template>
  <div class="flex justify-center items-center min-h-screen">
    <UForm
      :schema="schema"
      :state="state"
      class="space-y-4 p-8 shadow-lg rounded-md bg-gray-300 dark:bg-gray-800"
      @submit="onSubmit"
    >
      <h1 class="text-4xl font-bold text-center">Login</h1>
      <UFormGroup label="Usuário" name="username">
        <UInput v-model="state.username" placeholder="Digite seu usuário" />
      </UFormGroup>

      <UFormGroup label="Senha" name="password">
        <UInput
          v-model="state.password"
          type="password"
          placeholder="Digite sua senha"
        />
      </UFormGroup>

      <UButton
        type="submit"
        icon="i-clarity-login-line"
        block
        :loading="isSubmitting"
      >
        Entrar
      </UButton>
    </UForm>
  </div>
</template>
