<script setup lang="ts">
  import type { FormSubmitEvent } from '#ui/types'
  import { z } from 'zod'

  definePageMeta({
    middleware: 'auth',
  })

  const schema = z.object({
    username: z.string(),
    password: z.string().min(5, 'Senha tem no minimo 5 caracteres'),
  })

  type Schema = z.infer<typeof schema>

  const state = reactive({
    username: '',
    password: '',
  })

  const session = useAuth()

  const toast = useToast()

  const onSubmit = async (event: FormSubmitEvent<Schema>) => {
    const { username, password } = event.data

    const success = await session.login(username, password)
    if (success) {
      toast.add({
        title: 'Login efetuado com sucesso',
        icon: 'i-clarity-success-standard-line',
      })
      setTimeout(() => navigateTo('/'), 1000)
    }

    state.username = ''
    state.password = ''
  }
</script>

<template>
  <UContainer class="mt-32 flex justify-center items-center">
    <UForm
      :schema="schema"
      :state="state"
      class="space-y-4 max-w-xs w-full p-3"
      @submit="onSubmit"
    >
      <h1 class="text-3xl text-center">Login</h1>
      <UFormGroup label="Usuário" name="username">
        <UInput v-model="state.username" />
      </UFormGroup>

      <UFormGroup label="Password" name="password">
        <UInput v-model="state.password" type="password" />
      </UFormGroup>

      <UButton type="submit"> Submeter </UButton>
    </UForm>
  </UContainer>
</template>
