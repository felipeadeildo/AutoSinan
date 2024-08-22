<script setup lang="ts">
  defineProps<{ username: string }>()
</script>

<template>
  <div class="text-center mb-6">
    <h1 class="text-4xl font-extrabold mb-4">Olá, {{ username }}!</h1>
    <p class="text-lg dark:text-gray-300">
      Bem-vindo ao nosso sistema de automação de processos. Aqui, você pode
      selecionar e executar bots que otimizam tarefas em diversas plataformas,
      como o Sinan Online. Selecione um bot para começar, faça o upload dos
      dados necessários e deixe o resto com a nossa infraestrutura robusta de
      background, que cuidará de tudo para você, garantindo logs completos de
      cada etapa.
    </p>
  </div>
</template>
