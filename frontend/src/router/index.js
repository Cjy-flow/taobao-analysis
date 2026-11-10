import { createRouter, createWebHashHistory } from 'vue-router'
import Overview from '../views/Overview.vue'
import Behavior from '../views/Behavior.vue'
import Rfm from '../views/Rfm.vue'
import Predict from '../views/Predict.vue'

const routes = [
  { path: '/', redirect: '/overview' },
  { path: '/overview', name: 'overview', component: Overview, meta: { title: '仪表盘总览' } },
  { path: '/behavior', name: 'behavior', component: Behavior, meta: { title: '行为模式分析' } },
  { path: '/rfm', name: 'rfm', component: Rfm, meta: { title: 'RFM分群管理' } },
  { path: '/predict', name: 'predict', component: Predict, meta: { title: '预测模型监控' } }
]

export default createRouter({
  history: createWebHashHistory(),
  routes
})
