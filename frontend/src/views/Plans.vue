<template>
  <div class="plans-page">
    <van-nav-bar title="智能备考计划" />

    <van-cell-group inset title="第一步：基本信息">
      <van-field v-model="selectedCourseName" is-link readonly label="考试科目" placeholder="请选择" @click="showCoursePicker = true" />
      <van-field v-model="selectedGrade" is-link readonly label="当前年级" placeholder="请选择（可选）" @click="showGradePicker = true" />
      <van-field v-model="examDate" is-link readonly label="考试日期" placeholder="请选择" @click="showDatePicker = true" />
      <van-field v-model="targetScore" type="number" label="目标分数" placeholder="如 85" />
    </van-cell-group>

    <van-popup v-model:show="showGradePicker" position="bottom" round>
      <van-picker title="选择年级" :columns="gradeColumns" @confirm="onGradeConfirm" @cancel="showGradePicker = false" />
    </van-popup>

    <van-popup v-model:show="showCoursePicker" position="bottom" round>
      <van-picker title="选择课程" :columns="courseColumns" @confirm="onCourseConfirm" @cancel="showCoursePicker = false" />
    </van-popup>
    <van-popup v-model:show="showDatePicker" position="bottom" round>
      <van-date-picker title="选择考试日期" :min-date="minDate" v-model="currentDate" @confirm="onDateConfirm" @cancel="showDatePicker = false" />
    </van-popup>

    <div style="margin: 20px 16px">
      <van-button type="primary" block round :loading="generatingQuestionnaire" @click="startQuestionnaireFlow">
        开始多轮诊断（共3轮）
      </van-button>
    </div>

    <div v-if="doingQuestionnaire && currentQuestions.length > 0" class="questionnaire-section">
      <van-divider>第{{ round }}轮诊断：{{ roundTitles[round] }}</van-divider>
      <div class="questions-scroll-container">
        <van-cell-group inset v-for="q in currentQuestions" :key="q.id" class="question-card">
          <van-cell :title="`${q.id}. ${q.question}`" title-class="question-title" />
          
          <div class="options-group">
            <van-radio-group v-if="!q.type || q.type === 'single'" v-model="answers[q.id]" class="options-group">
              <van-radio v-for="(opt, idx) in q.options" :key="idx" :name="opt" class="custom-radio">{{ opt }}</van-radio>
            </van-radio-group>

            <van-checkbox-group v-else-if="q.type === 'multiple'" v-model="answers[q.id]" class="options-group">
              <van-checkbox v-for="(opt, idx) in q.options" :key="idx" :name="opt" shape="square" class="custom-radio">{{ opt }}</van-checkbox>
            </van-checkbox-group>

            <van-field v-else-if="q.type === 'text'" v-model="answers[q.id]" type="textarea" rows="2" autosize placeholder="请输入你的回答..." />
          </div>
          
        </van-cell-group>
      </div>
      <div style="margin: 20px 16px">
        <van-button type="success" block round @click="submitCurrentRound">
          {{ round < 3 ? '提交并进入下一轮' : '提交并生成详细计划' }}
        </van-button>
      </div>
    </div>

    <div v-if="savedPlan && savedPlan.daily_plan" class="plan-result">
      
      <div v-if="savedPlan.overall_advice" class="advice-section">
        <van-cell-group inset title="💡 导师专属备考建议">
          <div class="advice-content">
            {{ savedPlan.overall_advice }}
          </div>
        </van-cell-group>
      </div>

      <div v-if="savedPlan && savedPlan.daily_plan" class="dashboard-section">
        <van-cell-group inset>
          <div class="dashboard-content">
            <div class="dashboard-header">
              <span class="dashboard-title">🚀 备考火力值</span>
              <div style="display: flex; align-items: center; gap: 10px;">
                <van-button 
                  v-if="savedPlan && savedPlan.daily_plan"
                  size="mini" 
                  type="danger" 
                  plain 
                  icon="warning-o" 
                  :loading="isRescuing"
                  @click="handleRescue"
                >
                  进度告急
                </van-button>
                <span class="dashboard-stats">{{ completedTasks }} / {{ totalTasks }} 项微任务</span>
              </div>
            </div>
            
            <van-progress 
              :percentage="progressPercentage" 
              stroke-width="10" 
              color="linear-gradient(to right, #818CF8, #4F46E5)" 
              track-color="#E5E7EB"
            />
            
            <div class="heatmap-container">
              <span style="font-size: 12px; color: #6B7280; margin-bottom: 8px; display: block;">打卡热力图 (近{{ heatmapData.length }}天)</span>
              <div class="heatmap-grid">
                <div 
                  v-for="(day, index) in heatmapData" 
                  :key="index"
                  class="heatmap-square"
                  :class="`intensity-${day.intensity}`"
                  :title="`${day.date}: 强度 ${day.intensity}`"
                ></div>
              </div>
            </div>
          </div>
        </van-cell-group>
      </div>

      <van-divider>📅 每日实操计划（共 {{ Object.keys(savedPlan.daily_plan).length }} 天）</van-divider>
      <div style="padding: 0 16px; margin-bottom: 12px; text-align: right">
        <van-button size="small" type="danger" plain @click="deletePlan">删除计划</van-button>
      </div>
      <div class="plan-list">
        <div v-for="(task, date) in savedPlan.daily_plan" :key="date" class="plan-item" @click="openDailyDetail(date, typeof task === 'string' ? task : task)" style="cursor: pointer; position: relative;">
          <div class="plan-date">{{ formatDate(date) }}</div>
          <div class="plan-task">{{ typeof task === 'string' ? task : task }}</div>
          <van-icon name="arrow" style="position: absolute; right: 16px; top: 50%; transform: translateY(-50%); color: #ccc;" />
        </div>
      </div>
    </div>

    <van-popup v-model:show="showDailyPopup" position="bottom" round :style="{ height: '85%' }">
      <div style="padding: 20px;">
        
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; margin-top: 5px;">
          <h3 style="margin: 0; color: #4F46E5; font-size: 18px;">{{ selectedDate }} 执行清单</h3>
          <van-button 
            icon="replay" 
            size="small" 
            plain 
            type="primary" 
            color="#4F46E5"
            :loading="detailLoading"
            loading-text="重算中..."
            @click="promptRegenerate" 
          >
            换个计划
          </van-button>
        </div>

        <p style="color: #666; font-size: 14px; padding-bottom: 12px; border-bottom: 1px solid #eee; margin-top: 0;">
          <strong>今日主线：</strong>{{ selectedTask }}
        </p>
        
        <div style="text-align: center; padding: 40px 0;" v-if="detailLoading">
          <van-loading type="spinner" color="#4F46E5" vertical>AI 导师正在为你精算任务...</van-loading>
        </div>
        
        <div v-else style="margin-top: 10px;">
           <div v-if="dailyTasks.length > 0" class="interactive-tasks">
             <van-cell-group inset title="🎯 今日任务清单（点击打卡）">
               <van-cell v-for="task in dailyTasks" :key="task.id" clickable @click="task.done = !task.done; onTaskToggle(task)" v-show="shouldShowTask(task, selectedDateKey)">
                 <template #title>
                   <span 
                    :class="{ 'task-done-text': task.done }"
                    :style="{ 
                      color: task.isReview ? '#10B981' : '#333', 
                      fontWeight: task.isReview ? '600' : 'normal' 
                    }"
                  >
                    {{ task.text }}
                  </span>
                  <van-tag 
                    v-if="task.isReview" 
                    type="success" 
                    plain 
                    size="mini" 
                    style="margin-left: 6px; vertical-align: middle;"
                  >
                    抗遗忘
                  </van-tag>
                 </template>
                 <template #right-icon>
                   <div style="display: flex; align-items: center; gap: 12px;">
                     <van-icon 
                       v-if="!task.done" 
                       name="play-circle-o" 
                       size="22" 
                       color="#4F46E5" 
                       @click.stop="startFocus(task)" 
                     />
                     <van-checkbox v-model="task.done" @click.stop="onTaskToggle(task)" />
                   </div>
                 </template>
               </van-cell>
             </van-cell-group>
           </div>

           <van-divider>深度执行心法</van-divider>
           
           <MarkdownViewer :content="dailyDetailContent" />
        </div>
      </div>
    </van-popup>

    <van-popup v-model:show="showReportCard" round style="width: 85%; padding: 25px 20px; text-align: center; background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);">
      
      <div ref="posterRef" class="share-poster-hidden">
        <div class="poster-card">
          <div class="poster-header">
            <span class="poster-app-name">StudyMate</span>
            <span class="poster-date">{{ selectedDate }}</span>
          </div>
          
          <van-icon name="checked" color="#10B981" size="64" class="poster-main-icon" />
          <h1 class="poster-title">任务全歼！完美收官！</h1>
          <p class="poster-subtitle">你在《{{ selectedCourseName }}》的备考之路上又迈出了坚实一步！</p>
          
          <div class="poster-quote-block">
            <p class="poster-quote-content">“{{ currentDailyQuote }}”</p>
            <div class="poster-quote-footer">—— 你的 AI 专属助教</div>
          </div>
          
          <div class="poster-footer">
            <span class="poster-hint">#考研打卡 #自律 #高效备考</span>
            <span class="poster-brand">用 StudyMate，顶峰相见</span>
          </div>
        </div>
      </div>

      <van-icon name="checked" color="#10B981" size="60" />
      <h2 style="color: #333; margin: 15px 0 5px; font-size: 18px;">任务全歼！完美收官！</h2>
      <p style="color: #666; font-size: 14px; margin-bottom: 20px;">
        {{ selectedDate }} · {{ selectedCourseName }}
      </p>
      
      <div style="background: white; border-radius: 12px; padding: 15px; margin-bottom: 25px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); text-align: left;">
        <p style="margin: 0; font-size: 13px; color: #4b5563; line-height: 1.6;">
          "{{ currentDailyQuote }}"
        </p>
      </div>

      <div style="display: flex; gap: 10px;">
        <van-button 
          plain 
          round 
          block 
          icon="photo-o"
          color="#4F46E5" 
          :loading="isGeneratingPoster"
          loading-text="生成中..."
          @click="downloadSharePoster"
        >
          保存海报
        </van-button>
        <van-button 
          type="primary" 
          round 
          block 
          color="linear-gradient(to right, #4F46E5, #818CF8)" 
          @click="showReportCard = false"
        >
          收下荣誉
        </van-button>
      </div>
    </van-popup>

    <van-dialog 
      v-model:show="showCustomPrompt" 
      title="调整今日计划" 
      show-cancel-button 
      @confirm="executeRegenerate(customReqText)"
    >
      <div style="padding: 15px 20px;">
        <van-field 
          v-model="customReqText" 
          rows="2" 
          autosize 
          type="textarea" 
          placeholder="例：任务量减半、侧重背单词、增加实战演练..." 
          style="background-color: #f3f4f6; border-radius: 8px; padding: 10px;" 
        />
      </div>
    </van-dialog>

    <van-empty v-if="!savedPlan && !generatingPlan && !generatingQuestionnaire" description="填写信息后生成诊断问卷" />

    <!-- ====== 🍅 沉浸式专注模式全屏覆层 ====== -->
    <van-overlay :show="showTimer" z-index="9999" class="focus-overlay">
      <div class="focus-wrapper">
        <h2 class="focus-title">沉浸专注中</h2>
        <p class="focus-task-name">{{ timerTask?.text }}</p>
        
        <div class="focus-clock" :class="{ 'clock-paused': !isTimerRunning }">
          {{ formattedTime }}
        </div>
        
        <p style="color: #6b7280; font-size: 13px; margin-bottom: 60px; letter-spacing: 1px;">
          💡 保持专注，请放下手机
        </p>

        <div class="focus-controls">
          <van-button 
            round 
            :icon="isTimerRunning ? 'pause' : 'play'" 
            type="primary" 
            color="#4F46E5" 
            size="large"
            style="width: 70px; height: 70px; font-size: 30px;"
            @click="toggleTimer"
          />
          <van-button 
            round 
            plain 
            icon="cross" 
            type="danger" 
            size="small"
            style="margin-top: 30px;"
            @click="quitTimer"
          >
            结束专注
          </van-button>
        </div>
      </div>
    </van-overlay>

    <!-- ====== 🍅 专注时长设置弹窗 ====== -->
    <van-dialog 
      v-model:show="showFocusSetup" 
      title="设置专注时长" 
      show-cancel-button 
      @confirm="confirmStartFocus"
    >
      <div style="padding: 30px 20px; text-align: center;">
        <p style="margin-top: 0; margin-bottom: 25px; color: #666; font-size: 14px;">
          系统已根据任务自动识别建议时长<br>你可以手动调整：
        </p>
        <div style="display: flex; justify-content: center; align-items: center; gap: 10px;">
          <van-stepper 
            v-model="focusMinutesSetup" 
            min="1" 
            max="120" 
            step="5" 
            button-size="36px" 
            input-width="70px" 
          />
          <span style="font-weight: bold; color: #333;">分钟</span>
        </div>
      </div>
    </van-dialog>

    <van-overlay :show="generatingQuestionnaire || generatingPlan" @click.stop>
      <div class="loading-container">
        <van-loading type="spinner" size="48px" color="#4F46E5" vertical>
          {{ loadingText }}
        </van-loading>
      </div>
    </van-overlay>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, onBeforeUnmount } from 'vue'
import { showToast, showFailToast, showConfirmDialog } from 'vant'
import api from '../api'
import MarkdownViewer from '../components/MarkdownViewer.vue'
import confetti from 'canvas-confetti' // 引入撒花库
import html2canvas from 'html2canvas' // 【核心新增】：引入截图库

// 新增的状态变量
const dailyTasks = ref([]) // 提取出的任务数组
const showReportCard = ref(false) // 控制今日战报弹窗
const showCustomPrompt = ref(false)
const customReqText = ref('')
const currentDailyQuote = ref('') // 存放当次随机抽取的语录

// ====== 🍅 沉浸式番茄钟纯净版逻辑（已彻底移除白噪音，修复退出卡死Bug） ======
const showTimer = ref(false)
const showFocusSetup = ref(false)
const focusMinutesSetup = ref(25)
const pendingFocusTask = ref(null)

const timerTask = ref(null)
const timeLeft = ref(25 * 60)
const isTimerRunning = ref(false)
let timerInterval = null

const formattedTime = computed(() => {
  const m = String(Math.floor(timeLeft.value / 60)).padStart(2, '0')
  const s = String(timeLeft.value % 60).padStart(2, '0')
  return `${m}:${s}`
})

// 点击播放，自动提取时间并弹窗
const startFocus = (task) => {
  pendingFocusTask.value = task
  
  // 智能提取任务文本里的时间
  const matchRange = task.text.match(/\d+-(\d+)分钟/)
  const matchSingle = task.text.match(/(\d+)分钟/)
  
  if (matchRange) {
    focusMinutesSetup.value = parseInt(matchRange[1])
  } else if (matchSingle) {
    focusMinutesSetup.value = parseInt(matchSingle[1])
  } else {
    focusMinutesSetup.value = 25
  }
  
  showFocusSetup.value = true
}

// 确认时长，正式开启全屏专注
const confirmStartFocus = () => {
  if (timerInterval) clearInterval(timerInterval)
  
  timerTask.value = pendingFocusTask.value
  timeLeft.value = focusMinutesSetup.value * 60
  showTimer.value = true
  isTimerRunning.value = true
  showFocusSetup.value = false // 关闭时间选择弹窗

  timerInterval = setInterval(() => {
    if (timeLeft.value > 0) {
      timeLeft.value--
    } else {
      finishFocus()
    }
  }, 1000)
}

// 倒计时正常结束
const finishFocus = () => {
  if (timerInterval) clearInterval(timerInterval)
  showTimer.value = false
  isTimerRunning.value = false
  
  if (timerTask.value && !timerTask.value.done) {
    timerTask.value.done = true
    onTaskToggle(timerTask.value) // 自动触发打卡、保存本地、重算全盘进度
  }
}

// 暂停/继续切换
const toggleTimer = () => {
  if (isTimerRunning.value) {
    clearInterval(timerInterval)
    isTimerRunning.value = false
  } else {
    isTimerRunning.value = true
    timerInterval = setInterval(() => {
      if (timeLeft.value > 0) timeLeft.value--
      else finishFocus()
    }, 1000)
  }
}

// 中途强制退出
const quitTimer = () => {
  showConfirmDialog({ 
    title: '要放弃专注吗？', 
    message: '提前退出将不会自动记录打卡。',
    confirmButtonText: '残忍退出',
    cancelButtonText: '继续坚持',
    zIndex: 10000 // 【核心修复】：确保提示框浮在黑幕上方，不再卡死
  }).then(() => {
    if (timerInterval) clearInterval(timerInterval)
    showTimer.value = false
    isTimerRunning.value = false
  }).catch(() => {
    // 点击继续坚持，无事发生
  })
}

// 组件销毁生命周期清理
onBeforeUnmount(() => {
  if (timerInterval) clearInterval(timerInterval)
})

const posterRef = ref(null) // 【核心新增】：用于绑定海报 DOM 元素
const isGeneratingPoster = ref(false) // 用于保存按钮的 Loading 状态
const isRescuing = ref(false) // 控制抢救按钮的 loading 状态

// ====== 新增：战报鼓励语录库 ======
const quoteBank = [
  // 【基础与温情陪伴】
  "每一个划掉的待办事项，都是你向着理想分数迈出的坚实一步。保持这个节奏，顶峰相见！",
  "星光不问赶路人，时光不负有心人。今天的汗水，就是明天的底气！",
  "将来的你，一定会感谢现在拼命的自己。今日战役，干得漂亮！",
  "没有白走的路，每一步都算数。把平凡的一天坚持到底，就是伟大！",
  "极度自律的顶端是享受。恭喜你又享受了一个高效且充实的日子！",
  "行动是治愈焦虑的唯一解药。今日份的解药你已完美吸收！",
  "怕什么真理无穷，进一寸有一寸的欢喜。恭喜完美完成今日修炼！",
  "别认输，因为没人希望你赢。但你的 AI 导师，永远为你撑腰！",
  "那些看似不起波澜的日复一日，会突然在某一天让人看到坚持的意义。",
  "你今天的努力，是给明天的自己最好的礼物。收下荣誉，继续前行！",

  // 【东方古典哲思】
  "千淘万漉虽辛苦，吹尽狂沙始到金。 —— 刘禹锡",
  "博观而约取，厚积而薄发。 —— 苏轼",
  "凡事皆有极困难之时，打得通的，便是好汉。 —— 曾国藩",
  "道阻且长，行则将至；行而不辍，未来可期。 —— 《荀子》",
  "读书不觉已春深，一寸光阴一寸金。 —— 王贞白",
  "功崇惟志，业广惟勤。 —— 《尚书》",
  "不积跬步，无以至千里；不积小流，无以成江海。 —— 荀子",
  "天将降大任于斯人也，必先苦其心志，劳其筋骨。 —— 孟子",
  "锲而舍之，朽木不折；锲而不舍，金石可镂。 —— 荀子",
  "古之立大事者，不惟有超世之才，亦必有坚忍不拔之志。 —— 苏轼",
  "宝剑锋从磨砺出，梅花香自苦寒来。 —— 《警世贤文》",
  "有志者，事竟成，破釜沉舟，百二秦关终属楚。 —— 蒲松龄",
  "苦心人，天不负，卧薪尝胆，三千越甲可吞吴。 —— 蒲松龄",
  "长风破浪会有时，直挂云帆济沧海。 —— 李白",
  "盛年不重来，一日难再晨。及时当勉励，岁月不待人。 —— 陶渊明",
  "少年易老学难成，一寸光阴不可轻。 —— 朱熹",
  "莫等闲，白了少年头，空悲切。 —— 岳飞",
  "业精于勤，荒于嬉；行成于思，毁于随。 —— 韩愈",
  "三更灯火五更鸡，正是男儿读书时。 —— 颜真卿",
  "发奋识遍天下字，立志读尽人间书。 —— 苏轼",
  "立身以立学为先，立学以读书为本。 —— 欧阳修",
  "纸上得来终觉浅，绝知此事要躬行。 —— 陆游",
  "问渠那得清如许？为有源头活水来。 —— 朱熹",
  "咬定青山不放松，立根原在破岩中。 —— 郑燮",
  "穷且益坚，不坠青云之志。 —— 王勃",

  // 【西方先哲与现代巨匠】
  "It always seems impossible until it's done. (在事情未成功之前，一切总看似不可能。) —— 纳尔逊·曼德拉",
  "Success is the sum of small efforts, repeated day in and day out. (成功是日复一日微小努力的积累。) —— 罗伯特·科利尔",
  "The future belongs to those who believe in the beauty of their dreams. (未来属于那些相信梦想之美的人。) —— 埃莉诺·罗斯福",
  "Don't watch the clock; do what it does. Keep going. (不要老盯着钟表看，要像它一样，步履不停。) —— 山姆·莱文森",
  "Genius is 1% inspiration and 99% perspiration. (天才是1%的灵感，加99%的汗水。) —— 托马斯·爱迪生",
  "The only way to do great work is to love what you do. (成就伟大事业的唯一途径，就是热爱你所做的事。) —— 史蒂夫·乔布斯",
  "Believe you can and you're halfway there. (相信自己能做到，你就已经成功了一半。) —— 西奥多·罗斯福",
  "It does not matter how slowly you go as long as you do not stop. (走得多慢都无所谓，只要你绝不停下脚步。) —— 广为流传的西方名言",
  "Fall seven times and stand up eight. (跌倒七次，第八次站起来。) —— 日本谚语",
  "You don't have to be great to start, but you have to start to be great. (你不必等到足够强大才开始，但你必须开始才能强大。) —— 齐格·金克拉",
  "I find that the harder I work, the more luck I seem to have. (我发现我越努力，运气就越好。) —— 托马斯·杰斐逊",
  "The secret of getting ahead is getting started. (取得进展的秘诀在于开始行动。) —— 马克·吐温",
  "Education is the most powerful weapon which you can use to change the world. (教育是你用来改变世界的最强大的武器。) —— 纳尔逊·曼德拉",
  "What we learn with pleasure we never forget. (带着快乐学到的东西，我们永远不会忘记。) —— 阿尔弗雷德·梅西耶",
  "There is no elevator to success. You have to take the stairs. (通往成功的路上没有电梯，你必须一步步爬楼梯。) —— 齐格·金克拉",
  "Motivation is what gets you started. Habit is what keeps you going. (动力让你开始，习惯让你坚持。) —— 吉姆·罗恩",
  "Do what you can, with what you have, where you are. (在你所处的位置，用你拥有的资源，做你能做的事。) —— 西奥多·罗斯福",
  "Excellence is not an act, but a habit. (优秀不是一种行为，而是一种习惯。) —— 亚里士多德",
  "The expert in anything was once a beginner. (任何领域的专家都曾经是初学者。) —— 海伦·海斯",
  "Don’t let what you cannot do interfere with what you can do. (不要让你做不到的事，妨碍了你能做的事。) —— 约翰·伍登",
  "A year from now you may wish you had started today. (一年后的今天，你也许会希望自己是从今天开始的。) —— 凯伦·兰姆",
  "Strive for progress, not perfection. (追求进步，而不是完美。) —— 佚名",
  "You miss 100% of the shots you don't take. (如果你不挥棒，你百分之百会错过击球的机会。) —— 韦恩·格雷茨基",
  "Whether you think you can or you think you can't, you're right. (无论你认为自己行还是不行，你都是对的。) —— 亨利·福特",
  "The only place where success comes before work is in the dictionary. (成功唯一出现在努力之前的地方，是在字典里。) —— 维达尔·沙逊",

  // 【硬核备考与现代“毒鸡汤”】
  "那些让你熬夜受苦的题，最终都会变成你站在巅峰时的光环。",
  "不要假装努力，结果不会陪你演戏。真实的打卡最迷人！",
  "所谓的光辉岁月，并不是后来闪耀的日子，而是无人问津时，你对梦想的偏执。",
  "当你停下休息的时候，别忘了别人还在奔跑。今天的你，跑在了前面！",
  "最痛苦的时候，往往是你成长最快的时候。坚持住，你已经很棒了。",
  "备考就像在黑屋子里洗衣服，你不知道洗干净了没有，只能一遍遍去洗。今天你又搓洗了一次！",
  "放弃很容易，但坚持一定很酷。你今天酷毙了！",
  "你的对手在看书，你的朋友在减肥，你必须暗自拔尖！",
  "耐得住寂寞，才能守得住繁华。为你今天的极度专注点赞！",
  "没人能让你输，除非你不想赢。今天的你，赢下了这一局！",
  "如果你觉得现在走得辛苦，那就证明你在走上坡路。",
  "你背不下来的书，总有人能背下来；你做不出的题，总有人能做出来。别让那个人抢走你的位置。",
  "别在最能吃苦的年纪，选择了安逸。今天的汗水，是明天的铠甲。",
  "所有的一鸣惊人，其实都是厚积薄发。你正在积累爆发的能量。",
  "真正的学霸，不是不玩游戏，而是知道什么时候该放下手机。你做到了！",
  "每天多学一小时，考试多拿二十分。今天的投资，稳赚不赔！",
  "不要去想是否能够成功，既然选择了远方，便只顾风雨兼程。",
  "越努力，越幸运。你今天的幸运值已经拉满！",
  "宁愿辛苦一阵子，不要辛苦一辈子。今天流的汗，是明天流的泪折现。",
  "把每一天当成考前最后一天来拼，你一定会创造奇迹。",
  "学习如逆水行舟，不进则退。今天你划出了完美的一桨！",
  "你的名字那么好听，一定要出现在录取通知书上。",
  "只有极致的拼搏，才能配得上极致的风景。你正在攀登的路上。",
  "成功路上并不拥挤，因为坚持的人不多。恭喜你，还在队伍中。",
  "当你觉得自己为时已晚的时候，恰恰是最早的时候。",
  "既然认准了一条路，何必去打听要走多久。",
  "你的负担将变成礼物，你受的苦将照亮你的路。泰戈尔说得对，你做得也对。",
  "把懒惰放一边，把丧气的话收一收，把积极性提一提。你今天做得很棒！",
  "努力的意义就是：当好运降临的时候，你觉得你配得上。",
  "你现在流的每一滴汗，都是为了未来不留遗憾。",
  "没有所谓的天才，只有不曾放弃的凡人。致敬今天绝不放弃的你！",
  "别因为一时的挫折，就否定自己前面的所有努力。今天完美通关！",
  "高效，专注，自律。这三个词在今天的你身上体现得淋漓尽致。",
  "能够管理好自己时间的人，才能管理好自己的人生。",
  "今天的你，比昨天的你更强大。这就是学习的意义。",
  "不要让未来的你，讨厌现在的自己。今天的你，值得被未来的自己狠狠拥抱。",
  "任何值得去的地方，都没有捷径。感谢你今天踏踏实实走完了这段路。",
  "人生没有白走的路。今天多做的一道题，都是未来铺路的一块砖。",
  "向着月亮出发，即使不能到达，你也将置身于群星之中。",
  "你的自律，终将让你获得真正的自由。满载而归，明天继续！"
];

// ====== 新增：全局进度与热力图状态 ======
const totalTasks = ref(0)
const completedTasks = ref(0)
const progressPercentage = ref(0)
const heatmapData = ref([])

// ====== 📊 动态全局进度计算（时间结界版） ======
const updateGlobalProgress = () => {
  if (!selectedCourseId.value || !savedPlan.value) return

  // 1. 获取当天的绝对时间 (YYYY-MM-DD 格式)
  const today = new Date()
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`

  // 2. 读取本地缓存的任务状态
  const detailsKey = `study_plan_details_${String(selectedCourseId.value)}`
  const cachedDetails = JSON.parse(localStorage.getItem(detailsKey) || '{}')

  let total = 0
  let completed = 0
  const heatmap = []

  // 3. 遍历计划日历
  if (savedPlan.value.daily_plan) {
    Object.keys(savedPlan.value.daily_plan).forEach(dateStr => {
      
      // 【核心修改】：时间结界 —— 只统计"今天"以及"今天之前"的日子
      if (dateStr <= todayStr) {
        
        const dayCache = cachedDetails[dateStr]
        // 如果用户点开过那一天，生成了详细微任务
        if (dayCache && dayCache.tasks && dayCache.tasks.length > 0) {
          total += dayCache.tasks.length
          completed += dayCache.tasks.filter(t => t.done).length
          
          // 计算当天的完成强度 (0 到 4 级)
          const ratio = dayCache.tasks.filter(t => t.done).length / dayCache.tasks.length
          let intensity = 0
          if (ratio === 0) intensity = 1      // 有任务但没做
          else if (ratio < 0.5) intensity = 2 // 做了一半以下
          else if (ratio < 1) intensity = 3   // 做了一半以上
          else intensity = 4                  // 全歼
          
          heatmap.push({ date: dateStr, intensity })
        } else {
          // 哪怕用户连点都没点开过（未生成缓存），这天的任务也算作拖欠（算入总任务，完成为0）
          // 这里默认没点开的日子计作 1 个宏观大任务的缺失
          total += 1
          heatmap.push({ date: dateStr, intensity: 1 })
        }
        
      }
    })
  }

  // 4. 更新响应式状态，驱动 UI 变化
  totalTasks.value = total
  completedTasks.value = completed
  progressPercentage.value = total === 0 ? 0 : Math.round((completed / total) * 100)
  heatmapData.value = heatmap
}

const selectedGrade = ref('')
const showGradePicker = ref(false)
const gradeColumns = [
  { text: '大一', value: 'G1' },
  { text: '大二', value: 'G2' },
  { text: '大三', value: 'G3' },
  { text: '大四', value: 'G4' },
  { text: '研究生', value: 'Postgraduate' },
  { text: '社会考生', value: 'Other' }
]

const roundTitles = {
  1: '基础大类与认知扫描',
  2: '复习偏好与倾向调研',
  3: '硬核学科水平测验（真题模拟）'
}

const courseColumns = ref([])
const selectedCourseName = ref('')
const selectedCourseId = ref(null)
const examDate = ref('')
const targetScore = ref(85)
const showCoursePicker = ref(false)
const showDatePicker = ref(false)
const minDate = new Date()
const currentDate = ref([new Date().getFullYear(), new Date().getMonth() + 1, new Date().getDate()])

const answers = ref({})
const generatingQuestionnaire = ref(false)
const generatingPlan = ref(false)
const loadingText = ref('正在生成问卷...')

const round = ref(1)
const allAnswers = ref([])
const currentQuestions = ref([])
const doingQuestionnaire = ref(false)

const savedPlan = ref(null)

// 日计划详情相关变量
const showDailyPopup = ref(false)
const detailLoading = ref(false)
const selectedDate = ref('')      // 显示格式，如 "5月17日 周六"
const selectedDateKey = ref('')    // 原始格式，如 "2025-05-17"
const selectedTask = ref('')
const dailyDetailContent = ref('')

const onGradeConfirm = ({ selectedOptions }) => {
  if (selectedOptions?.[0]) {
    selectedGrade.value = selectedOptions[0].text
    showGradePicker.value = false
  }
}

const fetchCourses = async () => {
  console.log("[前端] 发起课程请求: /courses/");
  try {
    const res = await api.get('/courses/')
    console.log("[前端] 接收到课程数据:", res);
    
    // 响应拦截器已处理，res 直接是数据
    const courseData = res
    if (Array.isArray(courseData) && courseData.length > 0) {
      courseColumns.value = courseData.map(c => ({ text: c.name, value: c.id }))
      console.log("[前端] 格式化后的课程列表:", courseColumns.value);
      
      if (!selectedCourseId.value) {
        selectedCourseId.value = courseData[0].id
        selectedCourseName.value = courseData[0].name
        console.log("[前端] 默认选中:", selectedCourseName.value, selectedCourseId.value);
        
        // 列出所有已保存的计划缓存
        console.log("[DEBUG] === 检查所有已保存的计划 ===");
        let foundPlans = []
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i)
          if (key.startsWith('study_plan_') && !key.includes('details')) {
            foundPlans.push(key)
            console.log(`  找到计划: ${key}`)
          }
        }
        
        if (foundPlans.length === 0) {
          console.log("[DEBUG] ❌ 未找到任何保存的计划")
        } else {
          console.log(`[DEBUG] ✅ 找到 ${foundPlans.length} 个保存的计划`)
        }
        
        loadPlan()
      }
    } else {
      courseColumns.value = []
      showToast('暂无课程，请先在"课程管理"中添加课程')
    }
  } catch (e) {
    console.error("[前端 ERROR] 获取课程失败:", e);
    showFailToast(`获取课程失败: ${e.message || e.code || '未知错误'}`);
  }
}

const onCourseConfirm = ({ selectedOptions }) => {
  if (selectedOptions?.[0]) {
    selectedCourseName.value = selectedOptions[0].text
    selectedCourseId.value = selectedOptions[0].value
    showCoursePicker.value = false
    loadPlan()
  }
}

const onDateConfirm = ({ selectedValues }) => {
  examDate.value = `${selectedValues[0]}-${String(selectedValues[1]).padStart(2, '0')}-${String(selectedValues[2]).padStart(2, '0')}`
  showDatePicker.value = false
}

const startQuestionnaireFlow = async () => {
  if (!selectedCourseId.value || !examDate.value) {
    showToast('请填写基本信息')
    return
  }
  // 自动清除旧缓存
  localStorage.removeItem(`study_plan_${String(selectedCourseId.value)}`)
  savedPlan.value = null
  round.value = 1
  allAnswers.value = []
  doingQuestionnaire.value = true
  await fetchNextQuestions()
}

const fetchNextQuestions = async () => {
  generatingQuestionnaire.value = true
  loadingText.value = `AI 正在深度构建第 ${round.value} 轮问卷（${roundTitles[round.value]}）...`
  try {
    const res = await api.post('/plans/next_questionnaire', {
      course_name: selectedCourseName.value,
      exam_date: examDate.value,
      target_score: parseFloat(targetScore.value),
      grade: selectedGrade.value,
      previous_answers: allAnswers.value,
      current_round: round.value,
      question_count: round.value === 3 ? 15 : 8
    })
    
    console.log("[前端] 问卷响应:", res);
    
    if (res?.error) {
      showFailToast(res.message || '问卷生成失败')
      currentQuestions.value = []
    } else {
      currentQuestions.value = res?.questions || []
      answers.value = {}
      currentQuestions.value.forEach(q => {
        if (q.type === 'multiple') {
          answers.value[q.id] = []
        } else {
          answers.value[q.id] = ''
        }
      })
    }
  } catch (e) {
    console.error("[前端 ERROR] 获取问卷失败:", e);
    showFailToast('问卷构建超时，请重试')
    currentQuestions.value = []
  } finally {
    generatingQuestionnaire.value = false
  }
}

const submitCurrentRound = async () => {
  const currentRoundAnswers = currentQuestions.value.map(q => {
    const answer = answers.value[q.id]
    if (q.type === 'multiple') {
      return { 
        id: q.id, 
        question: q.question,
        type: q.type,
        answer: Array.isArray(answer) && answer.length > 0 ? answer.join(',') : "跳过/未答",
        options: q.options
      }
    }
    return { 
      id: q.id, 
      question: q.question,
      type: q.type || 'single',
      answer: answer || "跳过/未答",
      options: q.options
    }
  })
  allAnswers.value.push({
    round: round.value,
    answers: currentRoundAnswers
  })

  if (round.value >= 3) {
    doingQuestionnaire.value = false
    await generateFinalPlan()
  } else {
    round.value++
    await fetchNextQuestions()
  }
}

const generateFinalPlan = async () => {
    generatingPlan.value = true
    loadingText.value = '🎉 诊断结束！AI 导师正在为你精算定制化每日备考计划，请稍候...'
    try {
      const res = await api.post('/plans/generate_from_answers', {
        course_id: selectedCourseId.value,
        course_name: selectedCourseName.value,
        exam_date: examDate.value,
        target_score: parseFloat(targetScore.value),
        daily_hours: 3,
        mastery: 5,
        weak_points: '',
        all_answers: allAnswers.value
      })
      
      // 响应拦截器已处理，res 直接是数据
      // 【核心修复 1】：强力拦截后端明确抛出的错误
      if (res?.error) {
        showFailToast({ message: res.message || 'AI 导师生成超时，请点击重试', duration: 4000 })
        return // 🚨 强行阻断，绝对不保存空数据
      }

      // 【核心修复 2】：双重保险，如果 AI 幻觉导致没有生成 daily_plan 字段，也予以拦截
      if (!res || !res.daily_plan) {
        showFailToast({ message: 'AI 生成的数据格式异常，请再试一次', duration: 3000 })
        return
      }
      
      // 只有在数据绝对安全的情况下，才提取并组装
      const planData = {
        exam_date: examDate.value,
        target_score: parseFloat(targetScore.value),
        overall_advice: res?.overall_advice || '💡 稳扎稳打，按照以下计划执行，你一定能行！',
        daily_plan: res?.daily_plan,
        phases: res?.phases
      }
    
    // 保存新计划到缓存（使用字符串类型确保键名一致）
    localStorage.setItem(`study_plan_${String(selectedCourseId.value)}`, JSON.stringify(planData))
    savedPlan.value = planData
    
    // 同时保存到数据库
    await savePlanToDB()
    
    updateGlobalProgress()
    showToast('个性化详细计划已生成')
    
  } catch (e) {
    console.error("[前端 ERROR] 生成计划失败:", e);
    showFailToast('网络请求失败或超时')
  } finally {
    generatingPlan.value = false
  }
}

// 点击某一天时的展开逻辑
const openDailyDetail = async (dateKey, task) => {
  // dateKey 是原始格式 "YYYY-MM-DD"，用于缓存查找
  selectedDateKey.value = dateKey
  // 显示格式用于 UI 展示
  selectedDate.value = formatDate(dateKey)
  selectedTask.value = task
  showDailyPopup.value = true
  
  const cacheKey = `study_plan_details_${String(selectedCourseId.value)}`
  let cachedDetails = JSON.parse(localStorage.getItem(cacheKey) || '{}')

  // 1. 【核心修改】：不要只判断 tasks.length > 0，要判断是否有"非复习"的普通任务
  const dayCache = cachedDetails[dateKey]
  const hasNormalTasks = dayCache && dayCache.tasks && dayCache.tasks.some(t => !t.isReview);

  if (hasNormalTasks) {
    // 如果有普通任务，说明已经生成过了，直接用
    dailyDetailContent.value = dayCache.markdown || ''
    dailyTasks.value = dayCache.tasks
    detailLoading.value = false
    return
  }

  // 2. 缓存未命中，或者只有复习任务没有普通任务，必须调用 AI 生成！
  detailLoading.value = true
  dailyDetailContent.value = ''
  dailyTasks.value = []
  try {
    const res = await api.post('/plans/daily_detail', {
      course_name: selectedCourseName.value,
      date: selectedDate.value,
      task_summary: task,
      custom_requirement: ''
    })
    
    // 响应拦截器已处理，res 直接是数据
    if (res?.error) {
      showFailToast(res.message)
      // 即使 API 失败，也要保留已有的复习任务
      if (dayCache && dayCache.tasks) {
        dailyTasks.value = dayCache.tasks
      }
    } else {
      dailyDetailContent.value = res?.detail || ''
      extractTasks(res?.detail || '')
      
      // 【核心修改 2】：当 AI 成功返回新任务时，进行时空融合
      // 提取出当前天早就被注入的抗遗忘任务（如果有的话）
      const existingReviewTasks = (dayCache && dayCache.tasks) 
        ? dayCache.tasks.filter(t => t.isReview) 
        : []
      
      // 把复习任务顶在最前面，后面跟着今天的新任务
      const mergedTasks = [...existingReviewTasks, ...dailyTasks.value]
      
      // 更新到视图并保存到本地 localStorage
      dailyTasks.value = mergedTasks
      cachedDetails[dateKey] = {
        markdown: res?.detail,
        tasks: mergedTasks
      }
      localStorage.setItem(cacheKey, JSON.stringify(cachedDetails))
    }
  } catch (e) {
    showFailToast('获取详情失败')
    // 即使 API 失败，也要保留已有的复习任务
    if (dayCache && dayCache.tasks) {
      dailyTasks.value = dayCache.tasks
    }
  } finally {
    detailLoading.value = false
  }
}

// 正则提取任务
const extractTasks = (markdown) => {
  // 正则匹配所有以 "- [ ] " 开头的行
  const regex = /-\s+\[\s*\]\s+(.+)/g;
  const tasks = [];
  let match;
  while ((match = regex.exec(markdown)) !== null) {
    tasks.push({ 
      id: Math.random().toString(36).substr(2, 9), 
      text: match[1].trim(), 
      done: false 
    });
  }
  dailyTasks.value = tasks;
}

// 【核心修改 3】：时间隐身滤镜
const shouldShowTask = (task, panelDateStr) => {
  // 1. 获取现实世界的今天 (YYYY-MM-DD)
  const today = new Date();
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
  
  // 2. 如果是普通任务，永远显示
  if (!task.isReview) return true;
  
  // 3. 如果是抗遗忘任务，只有当"面板日期 <= 今天"时才显示！
  // 这意味着：未来的抗遗忘任务在后台已经就位了，但直到那一天真正到来前，它会对用户保持隐身。
  return panelDateStr <= todayStr;
}

// ====== 新增：艾宾浩斯抗遗忘复习引擎 ======

// 辅助函数：安全计算日期递增 (YYYY-MM-DD)
const addDays = (dateStr, days) => {
  const date = new Date(dateStr)
  date.setDate(date.getDate() + days)
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

// 【核心修复 1】：接收第二个参数 baseDateStr（任务所属的计划日期）
const injectEbbinghausTasks = (originalTaskText, baseDateStr) => {
  if (!selectedCourseId.value || !savedPlan.value || !baseDateStr) return

  // 艾宾浩斯经典复习周期：1天后、3天后、7天后
  const reviewIntervals = [1, 3, 7]
  const maxDateStr = savedPlan.value.exam_date 
  const detailsKey = `study_plan_details_${String(selectedCourseId.value)}`
  const cachedDetails = JSON.parse(localStorage.getItem(detailsKey) || '{}')

  reviewIntervals.forEach(delay => {
    // 【核心修复 2】：使用任务专属的日期往后推算，而不是现实世界的今天
    const targetDate = addDays(baseDateStr, delay)
    
    // 如果复习日期超过了考试日期，则舍弃
    if (maxDateStr && targetDate > maxDateStr) return

    if (!cachedDetails[targetDate]) cachedDetails[targetDate] = { tasks: [] }
    if (!cachedDetails[targetDate].tasks) cachedDetails[targetDate].tasks = []

    const reviewTaskText = `♻️ [闪回追踪] 复习：${originalTaskText}`

    // 【优化】：每天最多只有一个复习任务，避免任务过多
    const hasReviewTask = cachedDetails[targetDate].tasks.some(t => t.isReview)
    
    if (!hasReviewTask) {
      // 如果当天还没有复习任务，才添加新的复习任务
      cachedDetails[targetDate].tasks.unshift({
        id: Math.random().toString(36).substr(2, 9),
        text: reviewTaskText,
        done: false,
        isReview: true 
      })
    } else {
      // 如果当天已经有复习任务，将新内容合并到已有复习任务中
      const existingReviewTask = cachedDetails[targetDate].tasks.find(t => t.isReview)
      if (existingReviewTask && !existingReviewTask.text.includes(originalTaskText)) {
        existingReviewTask.text += ` + ${originalTaskText}`
      }
    }
  })

  localStorage.setItem(detailsKey, JSON.stringify(cachedDetails))
}

// 勾选任务时的联动逻辑（升级为艾宾浩斯激活版）
const onTaskToggle = (task) => {
  if (task.done) {
    confetti({
      particleCount: 60,
      spread: 60,
      origin: { y: 0.8 },
      colors: ['#4F46E5', '#10B981', '#F59E0B']
    });
  }
  
  // 使用原始日期 key 进行缓存操作
  const cacheKey = `study_plan_details_${String(selectedCourseId.value)}`
  let cachedDetails = JSON.parse(localStorage.getItem(cacheKey) || '{}')
  if (cachedDetails[selectedDateKey.value]) {
    if (typeof cachedDetails[selectedDateKey.value] === 'string') {
      cachedDetails[selectedDateKey.value] = {
        markdown: cachedDetails[selectedDateKey.value],
        tasks: []
      }
    }
    cachedDetails[selectedDateKey.value].tasks = dailyTasks.value
    localStorage.setItem(cacheKey, JSON.stringify(cachedDetails))
  }
  
  // 【核心新增】：如果任务被勾选为完成，且它本身不是一个复习任务，则启动艾宾浩斯引擎
  if (task.done && !task.isReview) {
    
    // 【核心修复 3】：抓取当前面板正在显示的日期
    const baseDate = selectedDateKey.value; 
    
    // 将任务文本和基准日期一并传给引擎
    injectEbbinghausTasks(task.text, baseDate)
    
    // 升级提示文案，让时间跨度更清晰
    showToast({
      message: `🧠 引擎激活！该考点将在 ${baseDate} 之后的第1、3、7天进行追踪！`,
      wordBreak: 'break-all',
      duration: 3000,
      position: 'bottom'
    })
  }
  
  // 【核心修复】：在这里强制触发一次大盘数据重算！
  updateGlobalProgress()
  
  if (dailyTasks.value.length > 0 && dailyTasks.value.every(t => t.done)) {
    setTimeout(() => {
      triggerUltimateConfetti();
      
      // 【新增】：随机抽取一句鼓励语
      const randomIndex = Math.floor(Math.random() * quoteBank.length);
      currentDailyQuote.value = quoteBank[randomIndex];
      
      showReportCard.value = true;
    }, 800);
  }
}

// 终极全屏特效（全做完时触发）
const triggerUltimateConfetti = () => {
  const duration = 3000;
  const end = Date.now() + duration;
  const frame = () => {
    confetti({ particleCount: 5, angle: 60, spread: 55, origin: { x: 0 }, colors: ['#4F46E5', '#FFB800'] });
    confetti({ particleCount: 5, angle: 120, spread: 55, origin: { x: 1 }, colors: ['#4F46E5', '#FFB800'] });
    if (Date.now() < end) requestAnimationFrame(frame);
  };
  frame();
}

// ====== 新增：一键生成并下载战报海报 ======
const downloadSharePoster = async () => {
  if (!posterRef.value) return;
  
  // 1. 开启 Loading 状态
  isGeneratingPoster.value = true;
  showToast({ message: '正在绘制专属战报...', duration: 0, forbidClick: true });

  try {
    // 2. 调用 html2canvas 截图
    // 配置项解释：scale: 2 (提高清晰度用于打印或高清屏), useCORS: true (允许跨域图片，虽然目前没用上)
    const canvas = await html2canvas(posterRef.value, {
      scale: 2, 
      useCORS: true, 
      backgroundColor: '#ffffff', // 强制白色底，防止透明
      logging: false // 关闭日志
    });

    // 3. 将 Canvas 转化为 Base64 图片数据
    const imgData = canvas.toDataURL('image/png');

    // 4. 创建虚拟 <a> 标签触发浏览器下载
    const link = document.createElement('a');
    // 文件名格式：StudyMate_战报_日期.png
    link.download = `StudyMate_战报_${selectedDate.value.replace(/-/g, '')}.png`;
    link.href = imgData;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // 5. 成功反馈
    showToast({ message: '海报已保存，快去分享吧！', type: 'success' });
  } catch (e) {
    console.error("[海报生成失败]:", e);
    showFailToast('海报生成失败，请稍后重试');
  } finally {
    // 6. 关闭 Loading
    isGeneratingPoster.value = false;
  }
}

// ====== 新增：一键抢救核心逻辑 ======
const handleRescue = () => {
  showConfirmDialog({
    title: '🆘 进度告急抢救',
    message: '如果你最近落下了进度，AI 导师将为你保留过去的打卡荣誉，并把遗漏的核心任务重新压缩排布到剩下的时间里。是否立即重算？',
    confirmButtonText: '一键抢救',
    confirmButtonColor: '#ee0a24'
  }).then(async () => {
    isRescuing.value = true
    
    // 1. 获取本地时间的今天字符串 (YYYY-MM-DD)
    const today = new Date();
    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

    // 2. 智能收集之前落下的任务
    const missedTasks = [];
    const cacheKey = `study_plan_details_${String(selectedCourseId.value)}`;
    const cachedDetails = JSON.parse(localStorage.getItem(cacheKey) || '{}');
    
    if (savedPlan.value && savedPlan.value.daily_plan) {
      Object.entries(savedPlan.value.daily_plan).forEach(([d, taskSummary]) => {
        if (d < todayStr) {
          const dailyCache = cachedDetails[d];
          // 如果没缓存（没点开过）或者里面的微任务没有全部 done，就算作落下
          if (!dailyCache || !dailyCache.tasks || !dailyCache.tasks.every(t => t.done)) {
            missedTasks.push(taskSummary);
          }
        }
      });
    }

    try {
      // 3. 请求 AI 进行重算
      const res = await api.post('/plans/rescue_plan', {
        course_name: selectedCourseName.value,
        exam_date: savedPlan.value.exam_date,
        // 防止文本过长崩掉，只取前5个最核心的遗漏任务发给 AI
        missed_topics: missedTasks.slice(0, 5).join('；') 
      })

      // 响应拦截器已处理，res 直接是数据
      if (res?.error) {
         showFailToast(res.message)
         return
      }

      // 4. 【时空融合】：保留过去的记录，覆盖未来的计划
      const newPlan = res.daily_plan;
      savedPlan.value.overall_advice = res.overall_advice; // 替换为抢救寄语
      
      Object.keys(savedPlan.value.daily_plan).forEach(d => {
         if (d >= todayStr) {
            delete savedPlan.value.daily_plan[d]; // 抹除今天及以后的旧计划
         }
      });
      // 缝合 AI 给出的新未来
      Object.assign(savedPlan.value.daily_plan, newPlan);

      // 5. 保存并重绘画板
      localStorage.setItem(`study_plan_${String(selectedCourseId.value)}`, JSON.stringify(savedPlan.value));
      updateGlobalProgress();
      showToast('抢救成功！别灰心，从今天开始冲刺！');
      
    } catch (e) {
      showFailToast('网络波动，抢救失败');
    } finally {
      isRescuing.value = false;
    }
  }).catch(() => {
    // 点击取消，无事发生
  })
}

// 拦截弹窗逻辑：负责问用户想要怎么改
const promptRegenerate = () => {
  customReqText.value = ''
  showCustomPrompt.value = true
}

// 实际的生成逻辑（增加 customReq 参数传递）
const executeRegenerate = async (customReq = '') => {
  detailLoading.value = true
  dailyDetailContent.value = ''
  dailyTasks.value = []
  
  try {
    const res = await api.post('/plans/daily_detail', {
      course_name: selectedCourseName.value,
      date: selectedDate.value,
      task_summary: selectedTask.value,
      custom_requirement: customReq
    })
    
    // 响应拦截器已处理，res 直接是数据
    if (res?.error) {
      showFailToast(res.message)
    } else {
      dailyDetailContent.value = res?.detail || ''
      extractTasks(res?.detail || '')
      
      // 使用原始日期 key 进行缓存操作
      const cacheKey = `study_plan_details_${String(selectedCourseId.value)}`
      let cachedDetails = JSON.parse(localStorage.getItem(cacheKey) || '{}')
      cachedDetails[selectedDateKey.value] = {
        markdown: res?.detail,
        tasks: dailyTasks.value
      }
      localStorage.setItem(cacheKey, JSON.stringify(cachedDetails))
      
      updateGlobalProgress()
      showToast(customReq ? '已按你的要求定制新计划！' : '已为你随机换了一套新计划！')
    }
  } catch (e) {
    showFailToast('重新生成失败，请检查网络')
  } finally {
    detailLoading.value = false
  }
}

const loadPlan = async () => {
  if (!selectedCourseId.value) {
    console.log("[DEBUG] 课程ID为空，无法加载计划")
    return
  }

  console.log(`[DEBUG] 尝试加载计划: courseId=${selectedCourseId.value}, courseName=${selectedCourseName.value}`)

  // 优先从数据库加载计划
  try {
    const res = await api.get('/plans/get_plan', { params: { course_id: selectedCourseId.value } })
    console.log("[DEBUG] 从数据库获取计划:", res)
    
    if (res.success && res.data) {
      savedPlan.value = {
        exam_date: res.data.exam_date,
        target_score: res.data.target_score,
        daily_plan: res.data.daily_plan,
        overall_advice: res.data.overall_advice || ''
      }
      console.log(`[DEBUG] ✅ 从数据库加载计划成功: 包含 ${Object.keys(savedPlan.value.daily_plan).length} 天任务`)
      updateGlobalProgress()
      return
    }
  } catch (e) {
    console.log("[DEBUG] 从数据库加载失败:", e)
  }

  // 降级到 localStorage
  const cacheKey = `study_plan_${selectedCourseId.value}`
  const cached = localStorage.getItem(cacheKey)
  if (cached) {
    try {
      savedPlan.value = JSON.parse(cached)
      console.log(`[DEBUG] ✅ 从本地缓存加载计划成功: 包含 ${Object.keys(savedPlan.value?.daily_plan || {}).length} 天任务`)
      // 同时保存到数据库
      await savePlanToDB()
      updateGlobalProgress()
    } catch (e) { 
      console.log("[DEBUG] 计划解析失败:", e)
      savedPlan.value = null 
    }
  } else {
    console.log("[DEBUG] ❌ 未找到缓存的计划")
    savedPlan.value = null
  }
}

const savePlanToDB = async () => {
  if (!selectedCourseId.value || !savedPlan.value) return

  try {
    await api.post('/plans/save_plan', {
      course_id: selectedCourseId.value,
      user_id: 1,
      exam_date: savedPlan.value.exam_date,
      target_score: savedPlan.value.target_score,
      daily_plan: JSON.stringify(savedPlan.value.daily_plan),
      overall_advice: savedPlan.value.overall_advice || ''
    })
    console.log("[DEBUG] 计划已保存到数据库")
  } catch (e) {
    console.log("[DEBUG] 保存到数据库失败:", e)
  }
}

const formatDate = (dateStr) => {
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}月${d.getDate()}日 周${['日','一','二','三','四','五','六'][d.getDay()]}`
}

const deletePlan = () => {
  showConfirmDialog({ title: '确认删除', message: '删除后将清空所有课程的旧计划缓存' })
    .then(() => {
      // 核弹级清理：删除所有 study_plan_ 开头的缓存项
      const keysToRemove = []
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key && key.startsWith('study_plan_')) {
          keysToRemove.push(key)
        }
      }
      keysToRemove.forEach(key => localStorage.removeItem(key))
      savedPlan.value = null
      showToast('已删除所有旧计划')
    }).catch(() => {})
}

onMounted(fetchCourses)
</script>

<style scoped>
.plans-page {
  height: 100%;
  background: var(--van-background-color);
  overflow-y: auto;
}

.advice-section {
  margin-bottom: 20px;
}
.advice-content {
  padding: 16px;
  font-size: 14px;
  color: #4b5563;
  line-height: 1.6;
  background-color: #f8fafc;
  border-left: 4px solid var(--van-primary-color);
}

.plan-list {
  padding: 0 16px;
}

.plan-item {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.plan-date {
  font-size: 14px;
  color: var(--van-primary-color);
  font-weight: bold;
  margin-bottom: 8px;
}

.plan-task {
  font-size: 15px;
  color: var(--van-text-color);
  line-height: 1.5;
}

.questionnaire-section {
  padding-bottom: 20px;
}

.questions-scroll-container {
  max-height: 60vh;
  overflow-y: auto;
  padding-bottom: 10px;
}

.question-card {
  margin-bottom: 16px;
  padding: 10px 0;
}

.question-title {
  font-weight: bold;
  color: #323233;
}

.options-group {
  padding: 10px 16px;
}

.custom-radio {
  margin-bottom: 12px;
  font-size: 14px;
  line-height: 1.4;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: rgba(255, 255, 255, 0.95);
  flex-direction: column;
}

.task-done-text {
  text-decoration: line-through;
  color: #9ca3af;
  transition: all 0.3s ease;
}

.interactive-tasks {
  margin-bottom: 20px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.08);
}

/* 📊 数据看板样式 */
.dashboard-section {
  margin-bottom: 20px;
}
.dashboard-content {
  padding: 16px;
  background: #ffffff;
}
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.dashboard-title {
  font-weight: bold;
  color: #111827;
  font-size: 15px;
}
.dashboard-stats {
  font-size: 13px;
  color: #4F46E5;
  font-weight: 600;
}
.heatmap-container {
  margin-top: 20px;
}
.heatmap-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.heatmap-square {
  width: 14px;
  height: 14px;
  border-radius: 3px;
  background-color: #ebedf0;
  transition: background-color 0.3s ease;
}

/* GitHub 经典绿配色 */
.intensity-0 { background-color: #ebedf0; }
.intensity-1 { background-color: #9be9a8; opacity: 0.4; }
.intensity-2 { background-color: #40c463; }
.intensity-3 { background-color: #30a14e; }
.intensity-4 { background-color: #216e39; box-shadow: 0 0 4px rgba(33, 110, 57, 0.4); }

/* ====== 📸 专属分享海报样式 (专门用于 html2canvas 截图) ====== */

/* 1. 将截图区域物理移出屏幕，防止干扰 UI */
.share-poster-hidden {
  position: fixed;
  left: -9999px;
  top: 0;
  z-index: -1;
}

/* 2. 定义海报卡片的尺寸和高档背景 (如 iPhone 屏幕比例) */
.poster-card {
  width: 375px; /* 标准移动端宽度 */
  height: 600px; /* 纵向长卡片 */
  padding: 30px;
  box-sizing: border-box;
  /* 优雅的紫蓝色渐变底图 */
  background: linear-gradient(160deg, #fdfbfb 0%, #ebedee 100%), 
              radial-gradient(at 10% 20%, rgba(79, 70, 229, 0.05) 0px, transparent 50%),
              radial-gradient(at 80% 80%, rgba(129, 140, 248, 0.05) 0px, transparent 50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  border: 1px solid #e5e7eb;
}

/* 3. 各模块的精致排版 */
.poster-header {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40px;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}
.poster-app-name {
  font-weight: bold;
  color: #4F46E5;
  font-size: 16px;
  letter-spacing: 1px;
}
.poster-date {
  color: #6B7280;
  font-size: 12px;
}
.poster-main-icon {
  margin-bottom: 20px;
  filter: drop-shadow(0 4px 6px rgba(16, 185, 129, 0.2));
}
.poster-title {
  margin: 0 0 10px 0;
  font-size: 24px;
  color: #111827;
  font-weight: 800;
  letter-spacing: -0.5px;
}
.poster-subtitle {
  margin: 0 0 40px 0;
  color: #6B7280;
  font-size: 13px;
  text-align: center;
  line-height: 1.5;
  padding: 0 10px;
}

/* 4. 语录块的高级感设计 */
.poster-quote-block {
  width: 100%;
  flex: 1;
  background-color: #ffffff;
  border-radius: 16px;
  padding: 25px;
  box-sizing: border-box;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.03), 0 4px 6px -2px rgba(0, 0, 0, 0.02);
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  border: 1px solid #f3f4f6;
}
/* 加上左右引号做装饰 */
.poster-quote-block::before {
  content: '“';
  position: absolute;
  top: 15px;
  left: 15px;
  font-size: 40px;
  color: rgba(79, 70, 229, 0.1);
  font-family: Georgia, serif;
}
.poster-quote-content {
  margin: 0 0 15px 0;
  font-size: 14px;
  color: #4b5563;
  line-height: 1.7;
  text-align: left;
  position: relative;
  z-index: 1;
}
.poster-quote-footer {
  width: 100%;
  text-align: right;
  font-size: 12px;
  color: #9ca3af;
  font-style: italic;
}

/* 5. 底部品牌与话题 */
.poster-footer {
  width: 100%;
  margin-top: 30px;
  border-top: 1px solid #eee;
  padding-top: 15px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}
.poster-hint {
  color: #818CF8;
  font-size: 11px;
}
.poster-brand {
  color: #9ca3af;
  font-size: 10px;
}

/* ====== 🍅 沉浸式专注模式样式 ====== */
.focus-overlay {
  background-color: rgba(17, 24, 39, 0.95); /* 深色护眼背景 */
  backdrop-filter: blur(8px); /* 毛玻璃效果 */
  display: flex;
  justify-content: center;
  align-items: center;
}
.focus-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  width: 90%;
}
.focus-title {
  color: #9ca3af;
  font-size: 16px;
  letter-spacing: 2px;
  font-weight: normal;
  margin-bottom: 20px;
}
.focus-task-name {
  color: #ffffff;
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 50px;
  line-height: 1.5;
  padding: 0 20px;
}
.focus-clock {
  font-size: 80px;
  font-weight: 800;
  font-family: 'Courier New', Courier, monospace;
  color: #818CF8;
  text-shadow: 0 0 20px rgba(79, 70, 229, 0.6);
  margin-bottom: 30px;
  transition: all 0.3s ease;
}
.clock-paused {
  color: #6b7280;
  text-shadow: none;
}
.focus-hint {
  color: #10B981;
  font-size: 14px;
  margin-bottom: 60px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.focus-controls {
  display: flex;
  flex-direction: column;
  align-items: center;
}
</style>
