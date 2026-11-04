<template>
  <div class="reviews-page">
    <div class="page-header">
      <h1>旅行评价</h1>
      <p>查看其他旅行者的真实评价，分享您的旅行体验</p>
    </div>

    <!-- 统计概览 -->
    <a-row :gutter="[24, 24]" class="stats-section">
      <a-col :span="6">
        <a-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon">
              <StarOutlined />
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ averageRating.toFixed(1) }}</div>
              <div class="stats-label">平均评分</div>
            </div>
          </div>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon">
              <TeamOutlined />
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ totalReviews }}</div>
              <div class="stats-label">总评价数</div>
            </div>
          </div>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon">
              <TrophyOutlined />
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ topDestinations }}</div>
              <div class="stats-label">热门目的地</div>
            </div>
          </div>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon">
              <LikeOutlined />
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ helpfulRate }}%</div>
              <div class="stats-label">有用率</div>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 筛选区域 -->
    <a-card class="filter-section">
      <a-row :gutter="[24, 24]" align="middle">
        <a-col :span="6">
          <a-input
            v-model:value="searchKeyword"
            placeholder="搜索目的地、用户或内容"
            allow-clear
            class="search-input"
          >
            <template #prefix>
              <SearchOutlined />
            </template>
          </a-input>
        </a-col>
        <a-col :span="6">
          <a-select
            v-model:value="destinationFilter"
            placeholder="选择目的地"
            allow-clear
            style="width: 100%"
          >
            <a-select-option value="">全部目的地</a-select-option>
            <a-select-option v-for="dest in uniqueDestinations" :key="dest" :value="dest">
              {{ dest }}
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-select
            v-model:value="ratingFilter"
            placeholder="评分筛选"
            allow-clear
            style="width: 100%"
          >
            <a-select-option value="">全部评分</a-select-option>
            <a-select-option value="5">5星</a-select-option>
            <a-select-option value="4">4星</a-select-option>
            <a-select-option value="3">3星</a-select-option>
            <a-select-option value="2">2星</a-select-option>
            <a-select-option value="1">1星</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-button type="primary" block @click="applyFilters">
            <template #icon>
              <FilterOutlined />
            </template>
            应用筛选
          </a-button>
        </a-col>
      </a-row>
    </a-card>

    <!-- 评价列表 -->
    <a-list
      :loading="loading"
      item-layout="vertical"
      size="large"
      :pagination="pagination"
      :data-source="filteredReviews"
    >
      <template #renderItem="{ item }">
        <a-list-item key="item.id" class="review-item">
          <template #actions>
            <span class="review-date">{{ formatDate(item.date) }}</span>
            <span class="review-helpful">
              <LikeOutlined /> {{ item.helpful }}
            </span>
            <span class="review-photos" v-if="item.photos && item.photos.length">
              <CameraOutlined /> {{ item.photos.length }}
            </span>
          </template>

          <div class="review-content">
            <div class="review-header">
              <div class="review-info">
                <a-avatar
                  :src="item.user.avatar"
                  class="user-avatar"
                />
                <div class="user-info">
                  <div class="user-name">{{ item.user.name }}</div>
                  <div class="user-level">{{ item.user.level }}</div>
                </div>
              </div>
              <div class="review-rating">
                <div class="stars">
                  <a-rate
                    v-model:value="item.rating"
                    disabled
                    :style="{ fontSize: '16px' }"
                  />
                </div>
                <div class="rating-text">
                  {{ getRatingText(item.rating) }}
                </div>
              </div>
            </div>

            <div class="review-details">
              <h3 class="review-title">{{ item.title }}</h3>
              <div class="review-destination">
                <EnvironmentOutlined />
                <span>{{ item.destination }}</span>
                <a-divider type="vertical" />
                <CalendarOutlined />
                <span>{{ item.travelDate }}</span>
              </div>
              <p class="review-text">{{ item.content }}</p>

              <!-- 亮点 -->
              <div class="highlights" v-if="item.highlights && item.highlights.length">
                <h4>旅行亮点：</h4>
                <div class="highlights-list">
                  <a-tag v-for="highlight in item.highlights" :key="highlight" color="blue">
                    {{ highlight }}
                  </a-tag>
                </div>
              </div>

              <!-- 照片 -->
              <div class="review-photos-section" v-if="item.photos && item.photos.length">
                <h4>旅行照片：</h4>
                <a-image-preview-group>
                  <div class="photos-grid">
                    <div
                      v-for="(photo, index) in item.photos"
                      :key="index"
                      class="photo-item"
                    >
                      <img
                        :src="photo"
                        :alt="`旅行照片 ${index + 1}`"
                        class="photo"
                      />
                    </div>
                  </div>
                </a-image-preview-group>
              </div>

              <!-- 标签 -->
              <div class="review-tags">
                <a-tag
                  v-for="tag in item.tags"
                  :key="tag"
                  :color="getTagColor(tag)"
                  class="tag"
                >
                  {{ tag }}
                </a-tag>
              </div>

              <!-- 回复 -->
              <div class="replies" v-if="item.replies && item.replies.length">
                <h4>回复：</h4>
                <div
                  v-for="reply in item.replies"
                  :key="reply.id"
                  class="reply-item"
                >
                  <div class="reply-header">
                    <a-avatar :src="reply.user.avatar" size="small" />
                    <span class="reply-user">{{ reply.user.name }}</span>
                    <span class="reply-date">{{ formatDate(reply.date) }}</span>
                  </div>
                  <p class="reply-content">{{ reply.content }}</p>
                </div>
              </div>

              <!-- 回复框 -->
              <a-comment v-model:value="replyContent">
                <template #actions>
                  <span @click="submitReply(item)">
                    <a-button type="link">回复</a-button>
                  </span>
                </template>
              </a-comment>
            </div>
          </div>
        </a-list-item>
      </template>
    </a-list>

    <!-- 写评价按钮 -->
    <div class="write-review-btn" v-if="userStore.isAuthenticated">
      <a-button
        type="primary"
        shape="round"
        size="large"
        @click="showWriteReview = true"
      >
        <template #icon>
          <EditOutlined />
        </template>
        写评价
      </a-button>
    </div>

    <!-- 写评价弹窗 -->
    <a-modal
      v-model:open="showWriteReview"
      title="写评价"
      :footer="null"
      width="800px"
      centered
    >
      <a-form
        ref="reviewFormRef"
        :model="reviewForm"
        :rules="reviewRules"
        layout="vertical"
        @finish="submitReview"
      >
        <a-row :gutter="[24, 0]">
          <a-col :span="24">
            <a-form-item label="目的地" name="destination">
              <a-input v-model:value="reviewForm.destination" placeholder="请输入旅行目的地" />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="旅行时间" name="travelDate">
              <a-date-picker
                v-model:value="reviewForm.travelDate"
                style="width: 100%"
                placeholder="选择旅行时间"
              />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="评分" name="rating">
              <a-rate
                v-model:value="reviewForm.rating"
                :tooltips="['极差', '失望', '一般', '满意', '惊喜']"
              />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="标题" name="title">
              <a-input
                v-model:value="reviewForm.title"
                placeholder="为您的评价起个标题"
                :max-length="50"
                show-count
              />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="评价内容" name="content">
              <a-textarea
                v-model:value="reviewForm.content"
                placeholder="分享您的旅行体验..."
                :rows="6"
                :max-length="1000"
                show-count
              />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="旅行亮点">
              <a-input-tag
                v-model:value="reviewForm.highlights"
                placeholder="添加旅行亮点"
              />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="标签">
              <a-select
                v-model:value="reviewForm.tags"
                mode="multiple"
                placeholder="选择标签"
                style="width: 100%"
              >
                <a-select-option value="风景优美">风景优美</a-select-option>
                <a-select-option value="交通便利">交通便利</a-select-option>
                <a-select-option value="服务周到">服务周到</a-select-option>
                <a-select-option value="物超所值">物超所值</a-select-option>
                <a-select-option value="值得一游">值得一游</a-select-option>
                <a-select-option value="特色美食">特色美食</a-select-option>
                <a-select-option value="历史文化">历史文化</a-select-option>
                <a-select-option value="自然风光">自然风光</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item>
              <a-button type="primary" html-type="submit" block>
                提交评价
              </a-button>
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import message from 'ant-design-vue/es/message'
import dayjs from 'dayjs'
import {
  SearchOutlined,
  FilterOutlined,
  LikeOutlined,
  CameraOutlined,
  EnvironmentOutlined,
  CalendarOutlined,
  EditOutlined,
  StarOutlined,
  TeamOutlined,
  TrophyOutlined
} from '@ant-design/icons-vue'
import type { FormInstance } from 'ant-design-vue'

const router = useRouter()
const userStore = useUserStore()

// 响应式数据
const loading = ref(false)
const searchKeyword = ref('')
const destinationFilter = ref('')
const ratingFilter = ref('')
const showWriteReview = ref(false)
const replyContent = ref('')
const reviewForm = ref({
  destination: '',
  travelDate: null,
  rating: 5,
  title: '',
  content: '',
  highlights: [] as string[],
  tags: [] as string[]
})
const reviewFormRef = ref<FormInstance>()
// 表单校验规则（静态展示页，字段无强制必填，留空规则对象）
const reviewRules = {}

// 分页
const pagination = ref({
  current: 1,
  pageSize: 10,
  total: 0
})

// 评价数据
const reviewsData = ref([
  {
    id: 1,
    title: '西藏之旅，心灵洗礼',
    content: '这次西藏之行让我深深感受到了高原的壮美和藏族文化的独特魅力。布达拉宫的雄伟、大昭寺的神圣、纳木错的纯净，都让我终身难忘。虽然高原反应有些难受，但看到这些美景，一切都值了！',
    rating: 5,
    date: '2024-01-15',
    destination: '西藏拉萨',
    travelDate: '2024-01-10',
    helpful: 128,
    photos: [
      'https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=400&h=300&fit=crop',
      'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=300&fit=crop',
      'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop'
    ],
    tags: ['风景优美', '历史文化', '值得一游'],
    highlights: ['布达拉宫', '大昭寺', '纳木错'],
    user: {
      name: '旅行达人小李',
      avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100&h=100&fit=crop',
      level: '资深旅行家'
    },
    replies: [
      {
        id: 1,
        user: {
          name: '用户小王',
          avatar: 'https://images.unsplash.com/photo-1494790108755-2616b612b786?w=100&h=100&fit=crop'
        },
        content: '说得真好！我也准备去西藏了，请问有什么需要注意的吗？',
        date: '2024-01-16'
      }
    ]
  },
  {
    id: 2,
    title: '张家界，阿凡达的取景地',
    content: '张家界的风景确实名不虚传！袁家界的山峰形态各异，云雾缭绕时如仙境一般。玻璃桥很刺激，天门山的索道体验也很好。唯一的遗憾是游客太多，拍照都要排队。',
    rating: 4,
    date: '2024-01-10',
    destination: '湖南张家界',
    travelDate: '2024-01-05',
    helpful: 95,
    photos: [
      'https://images.unsplash.com/photo-1566139886858-5491a3fa1c96?w=400&h=300&fit=crop',
      'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=300&fit=crop'
    ],
    tags: ['自然风光', '值得一游', '特色景点'],
    highlights: ['袁家界', '玻璃桥', '天门山'],
    user: {
      name: '户外探险家',
      avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop',
      level: '专业玩家'
    },
    replies: []
  },
  {
    id: 3,
    title: '成都，美食的天堂',
    content: '成都是个来了就不想走的城市！宽窄巷子的川菜、锦里的小吃、武侯祠的历史文化，都让人流连忘返。特别推荐火锅和串串香，麻辣鲜香，非常地道。',
    rating: 5,
    date: '2024-01-08',
    destination: '四川成都',
    travelDate: '2024-01-01',
    helpful: 156,
    photos: [
      'https://images.unsplash.com/photo-1544414400-2a4b311e236d?w=400&h=300&fit=crop',
      'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=300&fit=crop'
    ],
    tags: ['特色美食', '休闲度假', '历史文化'],
    highlights: ['宽窄巷子', '锦里', '武侯祠'],
    user: {
      name: '美食家小张',
      avatar: 'https://images.unsplash.com/photo-1494790108755-2616b612b786?w=100&h=100&fit=crop',
      level: '美食达人'
    },
    replies: [
      {
        id: 1,
        user: {
          name: '吃货一枚',
          avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100&h=100&fit=crop'
        },
        content: '强烈推荐！成都的小吃真的好吃到爆！',
        date: '2024-01-09'
      },
      {
        id: 2,
        user: {
          name: '游客小明',
          avatar: 'https://images.unsplash.com/photo-1494790108755-2616b612b786?w=100&h=100&fit=crop'
        },
        content: '锦里的小吃有哪些推荐的？',
        date: '2024-01-10'
      }
    ]
  },
  {
    id: 4,
    title: '三亚，热带天堂',
    content: '三亚的海滩真的很美，亚龙湾的沙子细腻，海水清澈见底。蜈支洲岛的水上项目很有趣，海底世界也很值得一看。不过旺季的人真的太多了，建议错峰出行。',
    rating: 4,
    date: '2024-01-05',
    destination: '海南三亚',
    travelDate: '2023-12-25',
    helpful: 87,
    photos: [
      'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=300&fit=crop',
      'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=300&fit=crop'
    ],
    tags: ['自然风光', '度假天堂', '海滩'],
    highlights: ['亚龙湾', '蜈支洲岛', '海底世界'],
    user: {
      name: '度假达人小王',
      avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop',
      level: '资深玩家'
    },
    replies: []
  }
])

// 计算属性
const totalReviews = computed(() => reviewsData.value.length)
const averageRating = computed(() => {
  const sum = reviewsData.value.reduce((acc, review) => acc + review.rating, 0)
  return sum / totalReviews.value
})
const topDestinations = computed(() => {
  const destCount = reviewsData.value.reduce((acc, review) => {
    acc[review.destination] = (acc[review.destination] || 0) + 1
    return acc
  }, {} as Record<string, number>)
  return Object.keys(destCount).length
})
const helpfulRate = computed(() => 85)

const uniqueDestinations = computed(() => {
  return Array.from(new Set(reviewsData.value.map(review => review.destination)))
})

const filteredReviews = computed(() => {
  let filtered = [...reviewsData.value]

  // 搜索关键词
  if (searchKeyword.value) {
    filtered = filtered.filter(review =>
      review.title.includes(searchKeyword.value) ||
      review.content.includes(searchKeyword.value) ||
      review.user.name.includes(searchKeyword.value)
    )
  }

  // 目的地筛选
  if (destinationFilter.value) {
    filtered = filtered.filter(review => review.destination === destinationFilter.value)
  }

  // 评分筛选
  if (ratingFilter.value) {
    filtered = filtered.filter(review => review.rating === parseInt(ratingFilter.value))
  }

  // 按日期排序
  filtered.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())

  pagination.value.total = filtered.length
  return filtered
})

// 方法
function formatDate(dateString: string) {
  return dayjs(dateString).format('YYYY-MM-DD')
}

function getRatingText(rating: number): string {
  const texts = {
    1: '极差',
    2: '失望',
    3: '一般',
    4: '满意',
    5: '惊喜'
  }
  return texts[rating as keyof typeof texts]
}

function getTagColor(tag: string): string {
  const colors: Record<string, string> = {
    '风景优美': 'green',
    '交通便利': 'blue',
    '服务周到': 'purple',
    '物超所值': 'orange',
    '值得一游': 'red',
    '特色美食': 'magenta',
    '历史文化': 'gold',
    '自然风光': 'cyan'
  }
  return colors[tag] || 'default'
}

function applyFilters() {
  pagination.value.current = 1
  message.success('筛选条件已应用')
}

function submitReply(review: any) {
  // 这里可以添加回复逻辑
  message.success('回复已提交')
  replyContent.value = ''
}

function submitReview() {
  // 这里可以提交评价
  message.success('评价已提交')
  showWriteReview.value = false
  reviewFormRef.value?.resetFields()
}

// 初始化
onMounted(() => {
  // 可以在这里加载评价数据
})
</script>

<style scoped>
.reviews-page {
  width: 100%;
  padding: 0 24px 32px;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
  padding: 40px 0;
  background: #f0f9ff;
  border-radius: 8px;
}

.page-header h1 {
  font-size: 32px;
  color: #0f172a;
  margin-bottom: 12px;
  font-weight: 600;
}

.page-header p {
  font-size: 16px;
  color: #64748b;
  margin: 0;
}

/* 统计卡片 */
.stats-section {
  margin-bottom: 32px;
}

.stats-card {
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.stats-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stats-icon {
  color: #0ea5e9;
  font-size: 24px;
}

.stats-info {
  flex: 1;
}

.stats-number {
  font-size: 24px;
  font-weight: 600;
  color: #0f172a;
  line-height: 1;
}

.stats-label {
  font-size: 12px;
  color: #64748b;
  margin-top: 4px;
}

/* 筛选区域 */
.filter-section {
  margin-bottom: 32px;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.search-input {
  border-radius: 8px;
}

/* 评价列表样式 */
.review-item {
  background: #ffffff;
  border-radius: 8px;
  margin-bottom: 16px;
  border: 1px solid #e2e8f0;
}

.review-item:hover {
  border-color: #cbd5e1;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.review-date {
  color: #64748b;
  font-size: 12px;
}

.review-helpful {
  color: #64748b;
  font-size: 12px;
  cursor: pointer;
}

.review-helpful:hover {
  color: #0ea5e9;
}

.review-photos {
  color: #64748b;
  font-size: 12px;
}

/* 评价内容 */
.review-content {
  padding: 24px;
}

.review-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.review-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-name {
  font-weight: 500;
  color: #0f172a;
}

.user-level {
  font-size: 12px;
  color: #64748b;
}

.review-rating {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.rating-text {
  font-size: 14px;
  color: #64748b;
}

.review-details {
  margin-top: 20px;
}

.review-title {
  font-size: 18px;
  font-weight: 500;
  color: #0f172a;
  margin-bottom: 12px;
}

.review-destination {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #64748b;
  font-size: 14px;
  margin-bottom: 16px;
}

.review-text {
  color: #334155;
  line-height: 1.6;
  margin-bottom: 20px;
}

.highlights {
  margin-bottom: 20px;
}

.highlights h4 {
  font-size: 16px;
  font-weight: 500;
  color: #0f172a;
  margin-bottom: 12px;
}

.highlights-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.review-photos-section {
  margin-bottom: 20px;
}

.review-photos-section h4 {
  font-size: 16px;
  font-weight: 500;
  color: #0f172a;
  margin-bottom: 12px;
}

.photos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
}

.photo-item {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
}

.photo {
  width: 100%;
  height: 120px;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.photo-item:hover .photo {
  transform: scale(1.05);
}

.review-tags {
  margin-bottom: 20px;
}

.tag {
  margin-right: 8px;
  margin-bottom: 8px;
}

.replies {
  margin-bottom: 20px;
}

.replies h4 {
  font-size: 16px;
  font-weight: 500;
  color: #0f172a;
  margin-bottom: 12px;
}

.reply-item {
  background: #f8fafc;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 12px;
}

.reply-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.reply-user {
  font-weight: 500;
  color: #0f172a;
}

.reply-date {
  color: #64748b;
  font-size: 12px;
}

.reply-content {
  color: #334155;
  line-height: 1.6;
}

/* 写评价按钮 */
.write-review-btn {
  position: fixed;
  bottom: 32px;
  right: 32px;
  z-index: 100;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .reviews-page {
    padding: 0 16px 24px;
  }

  .page-header {
    padding: 32px 16px;
  }

  .page-header h1 {
    font-size: 24px;
  }

  .stats-section {
    margin-bottom: 24px;
  }

  .stats-card {
    margin-bottom: 16px;
  }

  .review-content {
    padding: 20px;
  }

  .review-header {
    flex-direction: column;
    gap: 12px;
  }

  .review-rating {
    align-items: flex-start;
  }

  .photos-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  }

  .write-review-btn {
    bottom: 16px;
    right: 16px;
  }
}

@media (max-width: 576px) {
  .reviews-page {
    padding: 0 16px 24px;
  }

  .review-content {
    padding: 16px;
  }

  .photos-grid {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  }
}
</style>