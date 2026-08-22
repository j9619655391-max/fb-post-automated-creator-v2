import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import type { Organization } from '../api/organizations';
import { listMyOrganizations } from '../api/organizations';
import { useAuth } from './AuthContext';

interface OrgContextType {
    organizations: Organization[];
    currentOrg: Organization | null;
    setCurrentOrg: (org: Organization | null) => void;
    refreshOrganizations: () => Promise<void>;
    isLoading: boolean;
    isAdmin: boolean;
    isPro: boolean;
    isAgency: boolean;
}

const OrgContext = createContext<OrgContextType | undefined>(undefined);

export function OrgProvider({ children }: { children: ReactNode }) {
    const { isAuthenticated } = useAuth();
    const [organizations, setOrganizations] = useState<Organization[]>([]);
    const [currentOrg, setCurrentOrg] = useState<Organization | null>(() => {
        const storedId = window.localStorage.getItem('active_org_id');
        return storedId ? ({ id: Number(storedId) } as Organization) : null;
    });
    const [isLoading, setIsLoading] = useState(false);

    const refreshOrganizations = async () => {
        if (!isAuthenticated) {
            setOrganizations([]);
            setCurrentOrg(null);
            window.localStorage.removeItem('active_org_id');
            return;
        }
        setIsLoading(true);
        try {
            const orgs = await listMyOrganizations();
            setOrganizations(orgs);
            if (orgs.length > 0) {
                const storedId = Number(window.localStorage.getItem('active_org_id') || 0);
                const preferred = orgs.find(o => o.id === storedId) || (currentOrg && orgs.find(o => o.id === currentOrg.id));
                setCurrentOrg(preferred || orgs[0]);
            } else {
                setCurrentOrg(null);
            }
        } catch (error) {
            console.error('Failed to load organizations', error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        refreshOrganizations();
    }, [isAuthenticated]);

    useEffect(() => {
        if (currentOrg) window.localStorage.setItem('active_org_id', String(currentOrg.id));
    }, [currentOrg?.id]);

    const isPro = currentOrg?.subscription_tier === 'pro' || currentOrg?.subscription_tier === 'agency';
    const isAgency = currentOrg?.subscription_tier === 'agency';
    const isAdmin = true;

    return (
        <OrgContext.Provider value={{
            organizations,
            currentOrg,
            setCurrentOrg,
            refreshOrganizations,
            isLoading,
            isAdmin,
            isPro,
            isAgency,
        }}>
            {children}
        </OrgContext.Provider>
    );
}

export function useOrg() {
    const context = useContext(OrgContext);
    if (context === undefined) throw new Error('useOrg must be used within OrgProvider');
    return context;
}
