<template>
  <el-container class="layout">
    <el-aside width="220px" class="aside">
      <div class="logo">淘宝用户行为分析</div>
      <el-menu :default-active="$route.path" router class="menu" background-color="#1f2d3d"
               text-color="#c0ccda" active-text-color="#ffd04b">
        <el-menu-item index="/overview"><el-icon><DataLine/></el-icon><span>仪表盘总览</span></el-menu-item>
        <el-menu-item index="/behavior"><el-icon><PieChart/></el-icon><span>行为模式分析</span></el-menu-item>
        <el-menu-item index="/rfm"><el-icon><User/></el-icon><span>RFM分群管理</span></el-menu-item>
        <el-menu-item index="/predict"><el-icon><TrendCharts/></el-icon><span>预测模型监控</span></el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <span class="htitle">{{ $route.meta.title }}</span>
        <span class="muted">数据集：天池 UserBehavior（2017-11-25 ~ 2017-12-03）</span>
      </el-header>
      <el-main class="main"><router-view/></el-main>
    </el-container>
  </el-container>
</template>

<script setup>
</script>

<style scoped>
.layout { height: 100vh; }
.aside { background: #1f2d3d; }
.logo {
  height: 60px; line-height: 60px; text-align: center; color: #fff;
  font-size: 16px; font-weight: 700; background: #182234;
}
.menu { border-right: none; }
.header {
  background: #fff; display: flex; align-items: center; justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0,21,41,.08);
}
.htitle { font-size: 17px; font-weight: 600; color: #1f2d3d; }
.main { background: #f0f2f5; padding: 16px; overflow-y: auto; }
</style>
