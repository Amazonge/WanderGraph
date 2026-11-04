<template>
  <div class="recommendations-page">
    <div class="page-header">
      <h1>智能推荐</h1>
      <p>基于您的偏好和搜索历史，为您精心挑选的热门目的地</p>
    </div>

    <a-row :gutter="[24, 24]" class="recommendations-container">
      <!-- 推荐分类 -->
      <a-col :span="6" class="categories-sidebar">
        <a-card class="categories-card">
          <template #title>
            <span class="card-title">推荐分类</span>
          </template>
          <a-menu
            v-model:selectedKeys="selectedCategory"
            mode="vertical"
            style="border: none"
          >
            <a-menu-item key="all" class="category-item">
              <template #icon>
                <StarOutlined />
              </template>
              全部推荐
            </a-menu-item>
            <a-menu-item key="popular" class="category-item">
              <template #icon>
                <FireOutlined />
              </template>
              热门景点
            </a-menu-item>
            <a-menu-item key="cultural" class="category-item">
              <template #icon>
                🏛️
              </template>
              文化古迹
            </a-menu-item>
            <a-menu-item key="nature" class="category-item">
              <template #icon>
                <EnvironmentOutlined />
              </template>
              自然风光
            </a-menu-item>
            <a-menu-item key="food" class="category-item">
              <template #icon>
                <CoffeeOutlined />
              </template>
              美食之旅
            </a-menu-item>
            <a-menu-item key="adventure" class="category-item">
              <template #icon>
                ⚡
              </template>
              探险体验
            </a-menu-item>
          </a-menu>
        </a-card>

        <!-- 个性化标签 -->
        <a-card class="tags-card" style="margin-top: 16px">
          <template #title>
            <span class="card-title">个性标签</span>
          </template>
          <div class="tags-cloud">
            <a-tag
              v-for="tag in userTags"
              :key="tag"
              :class="{ active: selectedTags.includes(tag) }"
              @click="toggleTag(tag)"
              class="tag-item"
            >
              {{ tag }}
            </a-tag>
          </div>
        </a-card>
      </a-col>

      <!-- 推荐列表 -->
      <a-col :span="18">
        <!-- 排序和筛选 -->
        <div class="filter-bar">
          <a-space>
            <a-select
              v-model:value="sortBy"
              style="width: 150px"
              placeholder="排序方式"
            >
              <a-select-option value="popularity">热门度</a-select-option>
              <a-select-option value="rating">评分最高</a-select-option>
              <a-select-option value="newest">最新推荐</a-select-option>
              <a-select-option value="price">价格最优</a-select-option>
            </a-select>
            <a-select
              v-model:value="budget"
              style="width: 120px"
              placeholder="预算范围"
            >
              <a-select-option value="all">不限</a-select-option>
              <a-select-option value="budget">经济型</a-select-option>
              <a-select-option value="mid">中档</a-select-option>
              <a-select-option value="luxury">豪华</a-select-option>
            </a-select>
            <a-button type="primary" @click="applyFilters">
              <template #icon>
                <FilterOutlined />
              </template>
              应用筛选
            </a-button>
          </a-space>
        </div>

        <!-- 推荐卡片列表 -->
        <a-row :gutter="[24, 24]" class="recommendation-list">
          <a-col
            v-for="item in filteredRecommendations"
            :key="item.id"
            :span="8"
            class="recommendation-card-col"
          >
            <a-card
              hoverable
              class="recommendation-card"
              @click="viewDetails(item)"
            >
              <div class="card-image">
                <img
                  :src="item.image"
                  :alt="item.title"
                  class="recommendation-image"
                />
                <div class="card-overlay">
                  <div class="rating">
                    <StarFilled style="color: #ffd700" />
                    <span>{{ item.rating }}</span>
                  </div>
                </div>
              </div>
              <a-card-meta>
                <template #title>
                  <div class="card-title-container">
                    <h3 class="card-title">{{ item.title }}</h3>
                    <a-tag
                      :color="getTagColor(item.category)"
                      class="category-tag"
                    >
                      {{ getCategoryName(item.category) }}
                    </a-tag>
                  </div>
                </template>
                <template #description>
                  <div class="card-description">
                    <p>{{ item.description }}</p>
                    <div class="card-footer">
                      <div class="price">
                        <span class="price-label">均价:</span>
                        <span class="price-value">{{ item.price }}</span>
                        <span class="price-unit">/人</span>
                      </div>
                      <div class="location">
                        <EnvironmentOutlined style="color: #8c8c8c" />
                        <span>{{ item.location }}</span>
                      </div>
                    </div>
                    <div class="features">
                      <a-tag v-for="feature in item.features" :key="feature" size="small">
                        {{ feature }}
                      </a-tag>
                    </div>
                  </div>
                </template>
              </a-card-meta>
              <template #actions>
                <a-button
                  type="primary"
                  block
                  size="small"
                  @click.stop="addToPlan(item)"
                >
                  加入行程
                </a-button>
              </template>
            </a-card>
          </a-col>
        </a-row>

        <!-- 分页 -->
        <div class="pagination-container">
          <a-pagination
            v-model:current="currentPage"
            v-model:pageSize="pageSize"
            :total="totalItems"
            show-size-changer
            show-quick-jumper
            :show-total="(total, range) => `共 ${total} 条`"
            :page-size-options="['6', '12', '24', '48']"
            style="text-align: center"
          />
        </div>
      </a-col>
    </a-row>

    <!-- 详情弹窗 -->
    <a-modal
      v-model:open="detailModalOpen"
      :title="selectedRecommendation?.title"
      :footer="null"
      width="800px"
      centered
    >
      <div v-if="selectedRecommendation" class="detail-content">
        <div class="detail-image">
          <img
            :src="selectedRecommendation.image"
            :alt="selectedRecommendation.title"
            class="detail-img"
          />
        </div>
        <a-descriptions :column="2" bordered class="detail-info">
          <a-descriptions-item label="评分">
            <div class="rating-detail">
              <StarFilled style="color: #ffd700" />
              <span>{{ selectedRecommendation.rating }}</span>
              <span class="rating-count">({{ selectedRecommendation.reviewCount }}条评价)</span>
            </div>
          </a-descriptions-item>
          <a-descriptions-item label="价格">
            <span class="price-detail">{{ selectedRecommendation.price }}/人</span>
          </a-descriptions-item>
          <a-descriptions-item label="位置">
            <EnvironmentOutlined style="color: #8c8c8c" />
            <span>{{ selectedRecommendation.location }}</span>
          </a-descriptions-item>
          <a-descriptions-item label="最佳季节">
            <CalendarOutlined />
            <span>{{ selectedRecommendation.bestSeason }}</span>
          </a-descriptions-item>
          <a-descriptions-item label="推荐时长">
            <ClockCircleOutlined />
            <span>{{ selectedRecommendation.duration }}天</span>
          </a-descriptions-item>
          <a-descriptions-item label="适合人群">
            <TeamOutlined />
            <span>{{ selectedRecommendation.targetAudience }}</span>
          </a-descriptions-item>
        </a-descriptions>
        <div class="detail-description">
          <h4>详细介绍</h4>
          <p>{{ selectedRecommendation.fullDescription }}</p>
        </div>
        <div class="detail-highlights">
          <h4>亮点特色</h4>
          <ul>
            <li v-for="highlight in selectedRecommendation.highlights" :key="highlight">
              {{ highlight }}
            </li>
          </ul>
        </div>
        <div class="detail-actions">
          <a-button type="primary" size="large" block @click="addToPlan(selectedRecommendation)">
            加入我的行程
          </a-button>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import message from 'ant-design-vue/es/message'
import {
  StarOutlined,
  FireOutlined,
  EnvironmentOutlined,
  CoffeeOutlined,
  FilterOutlined,
  StarFilled,
  CalendarOutlined,
  ClockCircleOutlined,
  TeamOutlined
} from '@ant-design/icons-vue'

const router = useRouter()

// 状态管理
const selectedCategory = ref<string[]>(['all'])
const selectedTags = ref<string[]>([])
const sortBy = ref<string>('popularity')
const budget = ref<string>('all')
const currentPage = ref<number>(1)
const pageSize = ref<number>(12)
const detailModalOpen = ref<boolean>(false)
const selectedRecommendation = ref<any>(null)

// 用户标签
const userTags = [
  '自然风光',
  '历史文化',
  '美食探索',
  '休闲度假',
  '户外运动',
  '艺术熏陶',
  '亲子友好',
  '网红打卡'
]

// 推荐数据
const recommendationsData = ref([
  {
    id: 1,
    title: '西藏拉萨',
    category: 'cultural',
    description: '雪域高原上的圣城，感受藏族文化与宗教的神秘魅力',
    image: 'https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&h=600&fit=crop',
    rating: 4.8,
    reviewCount: 1234,
    price: '¥3800',
    location: '西藏自治区拉萨市',
    features: ['世界文化遗产', '藏传佛教圣地', '高原风光'],
    bestSeason: '5-10月',
    duration: '5-7天',
    targetAudience: '文化爱好者、摄影爱好者',
    fullDescription: '拉萨，西藏自治区的首府，被誉为"日光城"。这里有着深厚的历史文化底蕴，布达拉宫、大昭寺、罗布林卡等景点闻名于世。在这座海拔3650米的城市，你可以体验到独特的藏族文化，感受浓厚的宗教氛围。',
    highlights: [
      '布达拉宫：世界上海拔最高的宫殿，藏传佛教的圣地',
      '大昭寺：藏传佛教最神圣的寺庙之一',
      '八廓街：拉萨最古老的街道，体验藏族生活',
      '羊卓雍错：西藏三大圣湖之一，美如仙境',
      '纳木错：世界上海拔最高的咸水湖'
    ]
  },
  {
    id: 2,
    title: '张家界国家森林公园',
    category: 'nature',
    description: '奇峰林立，云雾缭绕的仙境，阿凡达取景地',
    image: 'https://images.unsplash.com/photo-1566139886858-5491a3fa1c96?w=800&h=600&fit=crop',
    rating: 4.7,
    reviewCount: 2156,
    price: '¥2800',
    location: '湖南省张家界市',
    features: ['世界地质公园', '5A级景区', '自然奇观'],
    bestSeason: '4-6月，9-11月',
    duration: '3-4天',
    targetAudience: '自然爱好者、户外探险',
    fullDescription: '张家界国家森林公园是中国第一个国家森林公园，以其独特的石英砂岩峰林地貌著称。这里峰林奇特，溪水清澈，森林茂密，被誉为"扩大的盆景，缩小的仙境"。电影《阿凡达》中的哈利路亚山就是在这里取景。',
    highlights: [
      '袁家界：电影《阿凡达》取景地',
      '天子山：观日出的最佳位置',
      '金鞭溪：清澈的溪流穿越峡谷',
      '十里画廊：最美的徒步路线',
      '黄石寨：张家界最大的观景台'
    ]
  },
  {
    id: 3,
    title: '成都宽窄巷子',
    category: 'food',
    description: '老成都的缩影，品尝地道川菜，体验慢生活',
    image: '/img/chengdu_xiangzi.jpg',
    rating: 4.6,
    reviewCount: 3421,
    price: '¥1500',
    location: '四川省成都市',
    features: ['历史文化', '美食天堂', '休闲购物'],
    bestSeason: '全年皆宜',
    duration: '2-3天',
    targetAudience: '美食爱好者、文化探索者',
    fullDescription: '宽窄巷子是成都三大历史文化保护区之一，由宽巷子、窄巷子和井巷子组成。这里是体验老成都生活的最佳去处，汇聚了成都的各种特色美食、手工艺品和民俗文化。',
    highlights: [
      '宽巷子：成都的"闲生活"代表',
      '窄巷子：成都的"慢生活"代表',
      '井巷子：成都的"新生活"代表',
      '川菜博物馆：了解川菜文化',
      '盖碗茶体验：品尝正宗成都茶文化'
    ]
  },
  {
    id: 4,
    title: '云南丽江古城',
    category: 'cultural',
    description: '纳西族文化的活化石，感受古城韵味',
    image: 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=800&h=600&fit=crop',
    rating: 4.5,
    reviewCount: 1876,
    price: '¥3200',
    location: '云南省丽江市',
    features: ['世界文化遗产', '纳西文化', '古城风貌'],
    bestSeason: '3-5月，9-11月',
    duration: '4-5天',
    targetAudience: '文化爱好者、摄影爱好者',
    fullDescription: '丽江古城是中国保存最完整的古城之一，有着800多年历史。这里融合了纳西族、汉族、白族等多民族文化，古城内水系发达，小桥流水，别具一格。',
    highlights: [
      '四方街：古城的中心广场',
      '木府：丽江古城的"紫禁城"',
      '黑龙潭公园：观古城全景',
      '束河古镇：比丽江古城更安静',
      '玉龙雪山：纳西族的神山'
    ]
  },
  {
    id: 5,
    title: '三亚亚龙湾',
    category: 'nature',
    description: '天下第一湾，椰风海韵，热带天堂',
    image: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop',
    rating: 4.9,
    reviewCount: 4567,
    price: '¥4500',
    location: '海南省三亚市',
    features: ['热带海滨', '5A级景区', '度假天堂'],
    bestSeason: '11月-次年4月',
    duration: '5-7天',
    targetAudience: '度假爱好者、海滩爱好者',
    fullDescription: '亚龙湾是三亚最美的海滩，有着7千米长的银白色沙滩，被誉为"天下第一湾"。这里海水清澈，沙质细腻，是度假、休闲、水上运动的天堂。',
    highlights: [
      '亚龙湾广场：看海上日出',
      '热带天堂森林公园：俯瞰整个海湾',
      '蝴蝶谷：观赏热带蝴蝶',
      '海底世界：探索海底奥秘',
      '天涯海角：浪漫的旅游胜地'
    ]
  },
  {
    id: 6,
    title: '九寨沟',
    category: 'nature',
    description: '童话世界，五彩斑斓的高山湖泊',
    image: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop',
    rating: 4.9,
    reviewCount: 3234,
    price: '¥4200',
    location: '四川省阿坝藏族羌族自治州',
    features: ['世界自然遗产', '人间仙境', '摄影天堂'],
    bestSeason: '4-5月，9-11月',
    duration: '2-3天',
    targetAudience: '自然爱好者、摄影爱好者',
    fullDescription: '九寨沟是中国著名的自然保护区，以翠海、叠瀑、彩林、雪峰、藏情、蓝冰"六绝"著称于世。这里的湖水色彩斑斓，如童话般美丽，是摄影爱好者的天堂。',
    highlights: [
      '五花海：九寨沟最美的海子',
      '珍珠滩瀑布：《西游记》取景地',
      '诺日朗瀑布：中国最宽的钙华瀑布',
      '长海：九寨沟最大的海子',
      '镜海：如镜面的湖面'
    ]
  }
])

// 计算属性
const totalItems = computed(() => recommendationsData.value.length)

const filteredRecommendations = computed(() => {
  let filtered = [...recommendationsData.value]

  // 分类筛选
  if (selectedCategory.value[0] !== 'all') {
    filtered = filtered.filter(item => item.category === selectedCategory.value[0])
  }

  // 标签筛选
  if (selectedTags.value.length > 0) {
    filtered = filtered.filter(item =>
      item.features.some(feature => selectedTags.value.includes(feature))
    )
  }

  // 预算筛选
  if (budget.value !== 'all') {
    const budgetMap = {
      budget: '¥2000',
      mid: '¥4000',
      luxury: '¥6000'
    }
    const maxPrice = budgetMap[budget.value]
    filtered = filtered.filter(item => {
      const priceNum = parseInt(item.price.replace(/[^0-9]/g, ''))
      const maxNum = parseInt(maxPrice.replace(/[^0-9]/g, ''))
      return priceNum <= maxNum
    })
  }

  // 排序
  filtered.sort((a, b) => {
    switch (sortBy.value) {
      case 'rating':
        return b.rating - a.rating
      case 'newest':
        return b.id - a.id
      case 'price':
        const priceA = parseInt(a.price.replace(/[^0-9]/g, ''))
        const priceB = parseInt(b.price.replace(/[^0-9]/g, ''))
        return priceA - priceB
      default: // popularity
        return b.reviewCount - a.reviewCount
    }
  })

  // 分页
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filtered.slice(start, end)
})

// 方法
function toggleTag(tag: string) {
  const index = selectedTags.value.indexOf(tag)
  if (index > -1) {
    selectedTags.value.splice(index, 1)
  } else {
    selectedTags.value.push(tag)
  }
}

function applyFilters() {
  currentPage.value = 1
  message.success('筛选条件已应用')
}

function viewDetails(item: any) {
  selectedRecommendation.value = item
  detailModalOpen.value = true
}

function addToPlan(item: any) {
  // 这里可以添加到行程的逻辑
  message.success(`已将 ${item.title} 加入行程`)
  detailModalOpen.value = false
}

function getTagColor(category: string): string {
  const colors = {
    popular: 'red',
    cultural: 'orange',
    nature: 'green',
    food: 'purple',
    adventure: 'blue'
  }
  return colors[category] || 'default'
}

function getCategoryName(category: string): string {
  const names = {
    popular: '热门景点',
    cultural: '文化古迹',
    nature: '自然风光',
    food: '美食之旅',
    adventure: '探险体验'
  }
  return names[category] || category
}

// 初始化
onMounted(() => {
  // 可以在这里加载用户偏好数据
})
</script>

<style scoped>
.recommendations-page {
  width: 100%;
  padding: 0 24px 32px;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
  padding: 40px 0;
  background: #f0f9ff;
  border-radius: 8px;
}

.page-header h1 {
  font-size: 32px;
  color: #0f172a;
  margin-bottom: 16px;
  font-weight: 600;
}

.page-header p {
  font-size: 16px;
  color: #64748b;
  margin: 0;
}

.recommendations-container {
  width: 100%;
}

/* 侧边栏样式 */
.categories-sidebar {
  position: sticky;
  top: 80px;
  height: fit-content;
}

.categories-card,
.tags-card {
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.categories-card .card-title,
.tags-card .card-title {
  color: #0f172a;
  font-weight: 500;
}

.category-item {
  margin: 4px 0;
  color: #334155;
  border-radius: 6px;
}

.category-item:hover {
  background: #f0f9ff !important;
}

.category-item.ant-menu-item-selected {
  background: #0ea5e9 !important;
  color: white !important;
}

.tags-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-item {
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid #e2e8f0;
  color: #64748b;
}

.tag-item:hover {
  border-color: #0ea5e9;
  color: #0ea5e9;
}

.tag-item.active {
  background: #0ea5e9;
  border-color: #0ea5e9;
  color: white;
}

/* 推荐列表样式 */
.filter-bar {
  margin-bottom: 24px;
}

.recommendation-list {
  display: grid;
}

.recommendation-card-col {
  transition: transform 0.3s ease;
}

.recommendation-card-col:hover {
  transform: translateY(-4px);
}

.recommendation-card {
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  height: 100%;
}

.recommendation-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.card-image {
  position: relative;
  height: 200px;
  overflow: hidden;
}

.recommendation-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.recommendation-card:hover .recommendation-image {
  transform: scale(1.05);
}

.card-overlay {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 14px;
}

.rating {
  display: flex;
  align-items: center;
  gap: 4px;
}

.card-title-container {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.card-title {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #0f172a;
}

.category-tag {
  border-radius: 4px;
  font-size: 12px;
}

.card-description {
  margin-top: 16px;
}

.card-description p {
  color: #64748b;
  margin-bottom: 16px;
  line-height: 1.6;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.price {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.price-label {
  color: #64748b;
  font-size: 12px;
}

.price-value {
  color: #0ea5e9;
  font-size: 18px;
  font-weight: 600;
}

.price-unit {
  color: #64748b;
  font-size: 12px;
}

.location {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #64748b;
  font-size: 14px;
}

.features {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.pagination-container {
  margin-top: 32px;
  display: flex;
  justify-content: center;
}

/* 详情弹窗样式 */
.detail-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.detail-image {
  width: 100%;
  height: 300px;
  border-radius: 12px;
  overflow: hidden;
}

.detail-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.detail-info {
  background: var(--bg-light);
}

.rating-detail {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rating-count {
  color: var(--text-secondary);
  font-size: 14px;
}

.price-detail {
  color: var(--primary-color);
  font-size: 18px;
  font-weight: 600;
}

.detail-description,
.detail-highlights {
  background: var(--bg-light);
  padding: 20px;
  border-radius: 12px;
}

.detail-description h4,
.detail-highlights h4 {
  margin: 0 0 12px 0;
  color: var(--text-color);
  font-weight: 500;
}

.detail-highlights ul {
  margin: 0;
  padding-left: 20px;
}

.detail-highlights li {
  margin-bottom: 8px;
  line-height: 1.6;
}

.detail-actions {
  display: flex;
  justify-content: center;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .categories-sidebar {
    position: static;
    margin-bottom: 32px;
  }

  .recommendation-card-col {
    span: 12;
  }
}

@media (max-width: 768px) {
  .recommendations-page {
    padding: 0 16px 24px;
  }

  .page-header {
    padding: 32px 16px;
    margin-bottom: 24px;
  }

  .page-header h1 {
    font-size: 24px;
  }

  .page-header p {
    font-size: 14px;
  }

  .filter-bar {
    flex-direction: column;
    gap: 16px;
  }

  .filter-bar .ant-select {
    width: 100%;
  }

  .recommendation-card-col {
    span: 24;
  }

  .categories-card,
  .tags-card {
    margin-bottom: 16px;
  }
}
</style>