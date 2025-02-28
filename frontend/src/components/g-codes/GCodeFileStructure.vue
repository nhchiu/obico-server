<template>
  <div class="gcodes-wrapper" :class="{ 'is-move-modal': isMoveModal }">
    <div
      v-if="!isMoveModal"
      class="header-panel"
      :class="{ 'without-action-buttons': !isCloud && !targetPrinter }"
    >
      <div class="text">Name</div>
      <div class="text">Size</div>
      <div class="text">Created</div>
      <div v-if="isCloud" class="text">Last Printed</div>
    </div>

    <div class="gcode-items-wrapper">
      <div>
        <file-structure-item
          v-for="(item, key) in [...folders, ...files]"
          v-show="
            (isFolder(item) && !searchStateIsActive) || (!isFolder(item) && !searchInProgress)
          "
          :key="`${isFolder(item) ? 'folder' : 'file'}_${key}`"
          :item="item"
          :is-cloud="isCloud"
          :target-printer="targetPrinter"
          :is-move-modal="isMoveModal"
          :disabled="disabledItem && disabledItem.id === item.id"
          @click="isFolder(item) ? $emit('openFolder', item) : $emit('openFile', item)"
          @renameItem="$emit('renameItem', item)"
          @moveItem="$emit('moveItem', item)"
          @deleteItem="$emit('deleteItem', item)"
          @print="$emit('print', item)"
        />
      </div>

      <mugen-scroll
        v-if="isCloud"
        :v-show="!isFolderEmpty"
        :handler="() => $emit('fetchMore')"
        :should-handle="!loading"
        class="text-center"
        :scroll-container="scrollContainerId"
      >
        <div v-if="!noMoreFolders || !noMoreFiles || searchInProgress" class="py-5">
          <b-spinner label="Loading..." />
        </div>
      </mugen-scroll>

      <div v-if="!isCloud && (localFilesLoading || searchInProgress)" class="text-center py-5">
        <b-spinner label="Loading..." />
      </div>
      <div v-else>
        <!-- Placeholders -->
        <div v-if="isFolderEmpty" class="placeholder text-secondary">
          <span>Nothing here yet</span>
        </div>
        <div v-else-if="nothingFound" class="placeholder text-secondary">
          <span>Nothing found</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import MugenScroll from 'vue-mugen-scroll'
import FileStructureItem from '@src/components/g-codes/FileStructureItem.vue'

export default {
  name: 'GCodeFileStructure',

  components: {
    MugenScroll,
    FileStructureItem,
  },

  props: {
    folders: {
      type: Array,
      default: () => [],
    },
    files: {
      type: Array,
      default: () => [],
    },
    noMoreFolders: {
      type: Boolean,
      default: false,
    },
    noMoreFiles: {
      type: Boolean,
      default: false,
    },
    loading: {
      type: Boolean,
      default: false,
    },
    localFilesLoading: {
      type: Boolean,
      default: false,
    },
    isCloud: {
      type: Boolean,
      default: true,
    },
    searchStateIsActive: {
      type: Boolean,
      default: false,
    },
    searchInProgress: {
      type: Boolean,
      default: false,
    },
    nothingFound: {
      type: Boolean,
      default: false,
    },
    targetPrinter: {
      type: Object,
      default: null,
    },
    scrollContainerId: {
      type: String,
      default: null,
    },
    isMoveModal: {
      type: Boolean,
      default: false,
    },
    disabledItem: {
      type: Object,
      default: null,
    },
  },

  computed: {
    isFolderEmpty() {
      return (
        !this.searchStateIsActive && !this.loading && !this.files.length && !this.folders.length
      )
    },
  },

  methods: {
    isFolder(item) {
      return !item.filename
    },
  },
}
</script>

<style lang="sass" scoped>
.gcodes-wrapper
  background-color: var(--color-surface-secondary)
  padding: 1em 2em
  border-radius: var(--border-radius-lg)
  &.is-move-modal
    padding: 0
    border-radius: 0

.header-panel
  display: flex
  padding: 1em calc(1em + 30px) 1em 1em
  border-bottom: 1px solid var(--color-divider)
  font-weight: bold
  &.without-action-buttons
    padding-right: 1em

  & > div
    flex: 1
    display: flex
    justify-content: space-between
    margin-left: 30px
    align-items: center
    font-size: 1rem

    &:first-child
      margin-left: 0
      flex: 3

  @media (max-width: 768px)
    &
      display: none

.placeholder
  margin: 5rem 0
  text-align: center
  &.text-secondary *
    color: var(--color-text-secondary)
</style>
