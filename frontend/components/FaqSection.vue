<script setup lang="ts">
  const faqs = ref([
    {
      label: 'O que é o AutoSinan?',
      icon: 'i-heroicons-information-circle',
      content:
        'O AutoSinan é uma plataforma de automação que facilita o gerenciamento e a busca de informações em sistemas de saúde pública como SINAN e GAL.',
    },
    {
      label: 'Como funciona o bot de investigação de pacientes?',
      icon: 'i-heroicons-arrow-down-tray',
      content:
        'O bot de investigação processa dados de planilhas ou arquivos CSV fornecidos pelo usuário e executa buscas automáticas no SINAN, retornando logs e status em tempo real pela interface web.',
    },
    {
      label: 'Como posso contribuir para o projeto?',
      icon: 'i-heroicons-user-group',
      content:
        'Você pode contribuir acessando o repositório no GitHub e enviando pull requests, reportando issues ou fornecendo sugestões.',
    },
    {
      label: 'Quais sistemas são suportados?',
      icon: 'i-heroicons-rectangle-group',
      content:
        'O AutoSinan suporta integração com sistemas como SINAN Online, SINAN Net, GAL, e outros sistemas de saúde pública brasileiros.',
    },
    {
      label: 'Qual é o objetivo principal do projeto?',
      icon: 'i-heroicons-square-3-stack-3d',
      content:
        'O objetivo principal é automatizar tarefas repetitivas e demoradas nos sistemas de saúde pública, permitindo que profissionais se concentrem em tarefas mais críticas.',
    },
    {
      label: 'Como posso acessar o suporte?',
      icon: 'i-heroicons-wrench-screwdriver',
      content:
        'Para suporte, você pode entrar em contato via Telegram, LinkedIn ou GitHub usando os links fornecidos na seção de contato.',
    },
  ])
</script>

<template>
  <UCard class="mb-8">
    <template #header>
      <h2 class="text-2xl font-semibold">FAQ</h2>
    </template>
    <UAccordion :items="faqs" />
  </UCard>
</template>
