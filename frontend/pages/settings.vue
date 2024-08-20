<script setup lang="ts">
  definePageMeta({
    requiresAuth: true,
    allowedRoles: ['user', 'admin'],
  })
</script>

<template>
  <div class="space-y-4">
    <h1 class="text-3xl font-bold">Configurações</h1>
    <p>
      Esta página ainda está em desenvolvimento, mas aqui estarão todas as
      configurações de variáveis dos Bots.
    </p>
    <ul class="list-disc space-y-2 pl-4">
      <li>Configurações de formas de reportar</li>
      <li>Configurações de autenticação dos bots em plataformas específicas</li>
      <li>
        Configurações de escolha de estratégias (por exemplo, qusis critérios
        utilizar ao filtrar por determinada coisa)
      </li>
      <li>Variáveis de "quantidade de tentativas"</li>
      <li>E muito mais...</li>
    </ul>
  </div>
</template>
