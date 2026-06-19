# 보호수 PlayMCP 개발 계획서

> 작성일: 2026-06-19  
> 버전: 0.1 (초안)

---

## 1. 프로젝트 개요

### 목적
국내 보호수(保護樹)에 대한 공공 데이터를 MCP 도구로 제공하여, AI 에이전트가 보호수 조회·분석·안내 기능을 수행할 수 있도록 한다.

### 포지셔닝
| 구분 | treeDoctor MCP | 보호수 MCP (본 프로젝트) |
|------|---------------|------------------------|
| 핵심 역할 | 수목 의사 (진단·처방) | 문화유산 수목 관리자 |
| 주요 데이터 | 병해충, 방제 정보 | 보호수 지정 현황, 위치, 이력 |
| 사용자 | 수목 관리 전문가 | 일반 시민, 산림 담당 공무원 |

---

## 2. 활용 공공 API

### 2-1. 핵심 API

| API 명 | 제공처 | 엔드포인트 | 주요 데이터 |
|--------|--------|-----------|------------|
| 보호수 현황 | 산림청 / 공공데이터포털 | `data.go.kr` | 지정번호, 수종, 수령, 위치, 지정일, 관리기관 |
| 국가생물종지식정보 | 국립생물자원관 | `species.nibr.go.kr` | 수종 학명, 생태 정보 |
| 국가공간정보 (V-World) | 국토정보공사 | `api.vworld.kr` | 좌표 → 행정구역 변환, 지도 타일 |
| 주소→좌표 변환 | 카카오맵 API | `dapi.kakao.com` | 지오코딩, 역지오코딩 |

### 2-2. 보조 API

| API 명 | 제공처 | 용도 |
|--------|--------|------|
| 기상청 단기예보 | 기상청 | 보호수 위치 기상 정보 제공 |
| 문화재청 천연기념물 | 문화재청 | 보호수 중 천연기념물 지정 여부 연동 |
| 국가표준식물목록 | 국립수목원 | 수종 정보 표준화 |

### 2-3. API 키 발급처
- 공공데이터포털: https://www.data.go.kr
- 카카오 개발자: https://developers.kakao.com
- V-World: https://www.vworld.kr
- 기상청 API허브: https://apihub.kma.go.kr

---

## 3. MCP 도구 목록 (Tools)

### 3-1. 조회 도구

#### `search_protected_trees`
주변 또는 지역명으로 보호수 목록 검색

```
입력:
  - location: string          # 시/도/구/동 또는 주소
  - radius_km: number         # 반경 (선택, 기본 5km)
  - species: string           # 수종 필터 (선택)
  - min_age: number           # 최소 수령 (선택)

출력:
  - trees[]: { id, name, species, age, location, lat, lng, managing_org }
```

---

#### `get_protected_tree_detail`
보호수 지정번호로 상세 정보 조회

```
입력:
  - tree_id: string           # 보호수 지정번호

출력:
  - 지정번호, 수종(국문/학명), 수령, 수고, 흉고둘레
  - 지정일, 지정사유, 소재지, 관리기관, 담당자 연락처
  - 좌표 (위경도), 사진 URL
  - 천연기념물 지정 여부
```

---

#### `get_tree_species_profile`
수종 기본 생태 정보 조회

```
입력:
  - species_name: string      # 수종명 (국문 또는 학명)

출력:
  - 학명, 분류, 원산지, 평균 수명
  - 생육 특성, 분포 지역
  - 보호수 지정된 동일 수종 건수
```

---

#### `get_protected_tree_stats`
지역·수종별 보호수 통계

```
입력:
  - region: string            # 시/도 (선택, 없으면 전국)
  - group_by: enum            # "species" | "region" | "age_range"

출력:
  - 총 건수, 그룹별 분포표
  - 평균 수령, 최고령 수목 정보
```

---

#### `find_nearby_protected_trees`
현재 좌표 기준 반경 내 보호수 탐색

```
입력:
  - lat: number
  - lng: number
  - radius_km: number         # 기본 3km

출력:
  - 거리순 정렬된 보호수 목록
  - 각 항목: 거리, 수종, 수령, 지정번호
```

---

### 3-2. 분석·안내 도구

#### `generate_tree_tour_route`
보호수 탐방 코스 생성

```
입력:
  - region: string            # 탐방 지역
  - max_trees: number         # 최대 방문 수 (기본 5)
  - transport: enum           # "walk" | "car"

출력:
  - 순서별 보호수 목록
  - 예상 이동 시간/거리
  - 각 보호수 간략 소개
```

---

#### `get_weather_at_tree_location`
보호수 위치 현재 기상 정보

```
입력:
  - tree_id: string

출력:
  - 현재 기온, 습도, 강수량
  - 방문 적합도 메시지
```

---

#### `check_cultural_heritage_status`
보호수의 문화재(천연기념물) 지정 여부 확인

```
입력:
  - tree_id: string

출력:
  - 천연기념물 지정번호 (있는 경우)
  - 지정 사유, 관련 문화재청 정보 URL
```

---

## 4. 기술 스택

| 구분 | 선택 | 비고 |
|------|------|------|
| 언어 | TypeScript | PlayMCP 표준 |
| MCP SDK | `@anthropic-ai/sdk` | MCP 서버 구현 |
| HTTP 클라이언트 | `axios` | 공공 API 호출 |
| 좌표 계산 | `geolib` | 반경 계산, 거리 정렬 |
| 캐싱 | 인메모리 (Map) | API 응답 TTL 캐시 (1시간) |
| 환경 변수 | `dotenv` | API 키 관리 |

---

## 5. 프로젝트 구조 (예상)

```
veteran_tree_mcp/
├── src/
│   ├── index.ts               # MCP 서버 진입점
│   ├── tools/
│   │   ├── search.ts          # search_protected_trees
│   │   ├── detail.ts          # get_protected_tree_detail
│   │   ├── species.ts         # get_tree_species_profile
│   │   ├── stats.ts           # get_protected_tree_stats
│   │   ├── nearby.ts          # find_nearby_protected_trees
│   │   ├── tour.ts            # generate_tree_tour_route
│   │   ├── weather.ts         # get_weather_at_tree_location
│   │   └── heritage.ts        # check_cultural_heritage_status
│   ├── api/
│   │   ├── publicData.ts      # 공공데이터포털 클라이언트
│   │   ├── kakaoMap.ts        # 카카오맵 API 클라이언트
│   │   ├── vworld.ts          # V-World API 클라이언트
│   │   ├── kma.ts             # 기상청 API 클라이언트
│   │   └── heritage.ts        # 문화재청 API 클라이언트
│   ├── cache/
│   │   └── ttlCache.ts        # TTL 기반 인메모리 캐시
│   └── types/
│       └── tree.ts            # 공통 타입 정의
├── .env.example
├── package.json
├── tsconfig.json
└── README.md
```

---

## 6. 개발 단계

### Phase 1 — MVP (핵심 조회)
- [ ] 공공데이터포털 보호수 API 연동
- [ ] `search_protected_trees` 구현
- [ ] `get_protected_tree_detail` 구현
- [ ] `find_nearby_protected_trees` 구현 (카카오맵 지오코딩)

### Phase 2 — 데이터 보강
- [ ] `get_tree_species_profile` 구현 (국가생물종 API)
- [ ] `get_protected_tree_stats` 구현
- [ ] `check_cultural_heritage_status` 구현 (문화재청 API)

### Phase 3 — 부가 기능
- [ ] `get_weather_at_tree_location` 구현 (기상청 API)
- [ ] `generate_tree_tour_route` 구현 (경로 최적화)
- [ ] 인메모리 TTL 캐시 적용

### Phase 4 — PlayMCP 배포
- [ ] PlayMCP 서버 패키징
- [ ] README 및 사용 예시 작성
- [ ] 카카오 채널 알림 연동 검토 (treeDoctor의 send_care_reminder 참고)

---

## 7. 주요 리스크 및 대응

| 리스크 | 대응 방안 |
|--------|----------|
| 공공 API 지역별 데이터 누락 | 결측 필드 graceful 처리, 제공 가능한 필드만 반환 |
| API 호출 제한 (일일 쿼터) | TTL 캐시로 중복 호출 최소화 |
| 좌표계 불일치 (WGS84 vs TM) | V-World 좌표 변환 API 활용 |
| 보호수 DB 갱신 주기 불일치 | 캐시 TTL을 24시간으로 설정, 출처·기준일 응답에 포함 |

---

## 8. 참고 데이터 현황

- 전국 보호수: 약 **16,000그루** (2023년 기준)
- 산림청 보호수 공공데이터: 공공데이터포털 등록 (`산림청_보호수 현황`)
- 천연기념물 지정 수목: 약 **270건** (문화재청)
