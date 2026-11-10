import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({ baseURL: '/api', timeout: 15000 })

http.interceptors.response.use(
  resp => {
    const body = resp.data
    if (body && typeof body === 'object' && 'code' in body) {
      if (body.code === 200) return body.data
      ElMessage.error(body.msg || '接口异常')
      return Promise.reject(new Error(body.msg))
    }
    return body
  },
  err => {
    ElMessage.error('请求失败：' + (err.response?.status || err.message))
    return Promise.reject(err)
  }
)

export default http
