import { Link } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import {
  FolderOpen, RefreshCw, Building, FileText, CheckCircle,
  Clock, ExternalLink, ChevronRight
} from 'lucide-react';
import { type ProjectWithSessions } from './types';

interface ProjectsSectionProps {
  projectData: ProjectWithSessions[];
  projectsLoading: boolean;
  onRefresh: () => void;
}

export function ProjectsSection({ projectData, projectsLoading, onRefresh }: ProjectsSectionProps) {
  return (
    <Card id="section-projects" className="scroll-mt-4">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FolderOpen className="w-5 h-5 text-pink-500" />
            프로젝트 현황
            {projectData.length > 0 && (
              <span className="text-sm font-normal text-muted-foreground">
                ({projectData.length}개)
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onRefresh}
              disabled={projectsLoading}
            >
              <RefreshCw className={`w-4 h-4 mr-1 ${projectsLoading ? 'animate-spin' : ''}`} />
              새로고침
            </Button>
            <Link to="/projects">
              <Button variant="outline" size="sm">
                전체 보기
              </Button>
            </Link>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {projectsLoading && projectData.length === 0 ? (
          <div className="text-center py-4 text-muted-foreground">
            프로젝트 로딩 중...
          </div>
        ) : projectData.length === 0 ? (
          <div className="text-center py-6 text-muted-foreground">
            <FolderOpen className="w-10 h-10 mx-auto mb-3 opacity-30" />
            <p>등록된 프로젝트가 없습니다.</p>
            <Link to="/projects" className="inline-flex items-center gap-1 mt-2 text-blue-600 hover:underline text-sm">
              프로젝트 생성하기
            </Link>
          </div>
        ) : (
          <>
            {/* 요약 통계 */}
            <div className="grid grid-cols-4 gap-3 mb-6">
              <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg text-center">
                <p className="text-xs text-muted-foreground">프로젝트</p>
                <p className="text-xl font-bold">{projectData.length}</p>
              </div>
              <div className="p-3 bg-blue-50 dark:bg-blue-950 rounded-lg text-center">
                <p className="text-xs text-muted-foreground">전체 세션</p>
                <p className="text-xl font-bold text-blue-600">
                  {projectData.reduce((s, d) => s + d.project.session_count, 0)}
                </p>
              </div>
              <div className="p-3 bg-green-50 dark:bg-green-950 rounded-lg text-center">
                <p className="text-xs text-muted-foreground">완료</p>
                <p className="text-xl font-bold text-green-600">
                  {projectData.reduce((s, d) => s + d.project.completed_count, 0)}
                </p>
              </div>
              <div className="p-3 bg-yellow-50 dark:bg-yellow-950 rounded-lg text-center">
                <p className="text-xs text-muted-foreground">대기</p>
                <p className="text-xl font-bold text-yellow-600">
                  {projectData.reduce((s, d) => s + d.project.pending_count, 0)}
                </p>
              </div>
            </div>

            {/* 프로젝트별 세션 목록 */}
            <div className="space-y-4">
              {projectData.map(({ project, sessions }) => {
                const progress = project.session_count > 0
                  ? Math.round((project.completed_count / project.session_count) * 100)
                  : 0;
                return (
                  <div key={project.project_id} className="border rounded-lg overflow-hidden">
                    {/* 프로젝트 헤더 */}
                    <a
                      href={`/bom/projects/${project.project_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-between p-4 bg-muted/30 hover:bg-muted/60 transition-colors"
                    >
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${
                          project.project_type === 'pid_detection' ? 'bg-cyan-100 dark:bg-cyan-900' : 'bg-pink-100 dark:bg-pink-900'
                        }`}>
                          <FolderOpen className={`w-4 h-4 ${
                            project.project_type === 'pid_detection' ? 'text-cyan-600' : 'text-pink-600'
                          }`} />
                        </div>
                        <div className="min-w-0">
                          <div className="font-semibold flex items-center gap-2">
                            {project.name}
                            <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded ${
                              project.project_type === 'pid_detection'
                                ? 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900 dark:text-cyan-300'
                                : 'bg-pink-100 text-pink-700 dark:bg-pink-900 dark:text-pink-300'
                            }`}>
                              {project.project_type === 'pid_detection' ? 'P&ID' : 'BOM'}
                            </span>
                          </div>
                          <div className="text-sm text-muted-foreground flex items-center gap-1">
                            <Building className="w-3 h-3" /> {project.customer}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 text-sm shrink-0 ml-4">
                        <div className="flex items-center gap-3 text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <FileText className="w-3.5 h-3.5" /> {project.session_count}
                          </span>
                          <span className="flex items-center gap-1 text-green-600">
                            <CheckCircle className="w-3.5 h-3.5" /> {project.completed_count}
                          </span>
                          <span className="flex items-center gap-1 text-yellow-600">
                            <Clock className="w-3.5 h-3.5" /> {project.pending_count}
                          </span>
                        </div>
                        {project.session_count > 0 && (
                          <div className="flex items-center gap-2 w-24">
                            <div className="flex-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-green-500 transition-all"
                                style={{ width: `${progress}%` }}
                              />
                            </div>
                            <span className="text-xs text-muted-foreground w-8 text-right">{progress}%</span>
                          </div>
                        )}
                        <ExternalLink className="w-4 h-4 text-blue-500" />
                        <ChevronRight className="w-4 h-4 text-muted-foreground" />
                      </div>
                    </a>

                    {/* 세션 목록 (최대 5개) */}
                    {sessions.length > 0 && (
                      <div className="divide-y">
                        {sessions.slice(0, 5).map((session) => (
                          <a
                            key={session.session_id}
                            href={`/bom/workflow?session=${session.session_id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center justify-between px-4 py-2.5 hover:bg-muted/30 transition-colors"
                          >
                            <div className="flex items-center gap-3 flex-1 min-w-0">
                              <FileText className="w-4 h-4 text-muted-foreground shrink-0" />
                              <span className="text-sm truncate">{session.filename}</span>
                            </div>
                            <div className="flex items-center gap-3 ml-4 shrink-0">
                              <span className="text-xs text-muted-foreground">
                                검출 {session.detection_count} · 검증 {session.verified_count}
                              </span>
                              <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                                session.status === 'completed'
                                  ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                                  : session.status === 'error'
                                    ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                                    : 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                              }`}>
                                {session.status === 'completed' ? '완료' : session.status}
                              </span>
                              <ExternalLink className="w-3.5 h-3.5 text-muted-foreground" />
                            </div>
                          </a>
                        ))}
                        {sessions.length > 5 && (
                          <a
                            href={`/bom/projects/${project.project_id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center justify-center py-2.5 text-sm text-blue-600 hover:bg-muted/30 transition-colors"
                          >
                            + {sessions.length - 5}개 더 보기
                          </a>
                        )}
                      </div>
                    )}
                    {sessions.length === 0 && (
                      <div className="px-4 py-3 text-sm text-muted-foreground">
                        세션이 없습니다.
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
