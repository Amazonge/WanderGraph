<template>
  <div ref="mapContainer" :style="{ width: '100%', height: height }" />
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'

interface MapAttraction {
  name: string
  lat: number
  lng: number
}

const props = withDefaults(
  defineProps<{
    attractions?: MapAttraction[]
    height?: string
  }>(),
  {
    attractions: () => [],
    height: '400px',
  },
)

const mapContainer = ref<HTMLElement>()
let map: any = null
let AMapRef: any = null
const isReady = ref(false)

async function initMap() {
  try {
    const AMapLoader = (await import('@amap/amap-jsapi-loader')).default
    const key = import.meta.env.VITE_AMAP_KEY || ''
    if (!key) {
      console.warn('VITE_AMAP_KEY 未配置，地图将不可用')
      if (mapContainer.value) {
        mapContainer.value.innerHTML =
          '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#999">地图未配置（需要 VITE_AMAP_KEY）</div>'
      }
      return
    }

    AMapRef = await AMapLoader.load({
      key,
      version: '2.0',
      plugins: ['AMap.MarkerCluster'],
    })

    if (mapContainer.value) {
      map = new AMapRef.Map(mapContainer.value, {
        zoom: 12,
        center: [104.0668, 30.5728],
        viewMode: '3D',
      })
      isReady.value = true
    }
  } catch (e) {
    console.error('高德地图加载失败', e)
  }
}

function addMarkers(items: MapAttraction[]) {
  if (!map || !AMapRef) return

  map.clearMap()

  const markers = items.map((item) => {
    return new AMapRef.Marker({
      position: [item.lng, item.lat],
      title: item.name,
      label: {
        content: `<div style="font-size:12px;padding:2px 6px;background:#fff;border-radius:4px;box-shadow:0 1px 3px rgba(0,0,0,.2)">${item.name}</div>`,
        offset: new AMapRef.Pixel(-20, -30),
      },
    })
  })

  map.add(markers)

  if (markers.length > 0) {
    map.setFitView(markers)
  }
}

watch(
  () => props.attractions,
  (items) => {
    if (isReady.value && items?.length) {
      addMarkers(items)
    }
  },
  { deep: true },
)

onMounted(async () => {
  await initMap()
  if (props.attractions.length) {
    addMarkers(props.attractions)
  }
})

onUnmounted(() => {
  if (map) {
    map.destroy()
    map = null
  }
})
</script>
